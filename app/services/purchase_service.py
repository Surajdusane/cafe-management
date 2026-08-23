from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.purchase import Purchase, PurchaseItem
from app.services.supplier_service import validate_supplier_exists


def _round(value: float) -> float:
    return round(value, 2)


def compute_line_total(quantity: float, unit_cost: float) -> float:
    """Pure money formula for one line so it can be unit-tested without a DB."""
    return _round(quantity * unit_cost)


def list_purchases(
    db: Session,
    search: str | None = None,
    supplier_id: int | None = None,
    payment_status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Purchase]:
    stmt = select(Purchase).options(selectinload(Purchase.items))
    conditions = []
    if search:
        term = f"%{search.strip()}%"
        conditions.append(
            or_(Purchase.purchase_number.ilike(term), Purchase.supplier_name.ilike(term))
        )
    if supplier_id is not None:
        conditions.append(Purchase.supplier_id == supplier_id)
    if payment_status:
        conditions.append(Purchase.payment_status == payment_status)
    if start_date is not None:
        conditions.append(Purchase.purchase_date >= start_date)
    if end_date is not None:
        conditions.append(Purchase.purchase_date <= end_date)
    if conditions:
        stmt = stmt.where(*conditions)
    # Newest purchases first — staff care about the latest deliveries.
    stmt = stmt.order_by(Purchase.purchase_date.desc(), Purchase.id.desc())
    return list(db.scalars(stmt))


def summarize(purchases: list[Purchase]) -> dict:
    """Stat-card totals over the filtered result set."""
    total_amount = _round(sum(p.total for p in purchases))
    unpaid = [p for p in purchases if p.payment_status == "Unpaid"]
    return {
        "count": len(purchases),
        "total_amount": total_amount,
        "unpaid_count": len(unpaid),
        "unpaid_amount": _round(sum(p.total for p in unpaid)),
    }


def get_purchase_or_404(db: Session, purchase_id: int) -> Purchase:
    stmt = (
        select(Purchase)
        .options(selectinload(Purchase.items))
        .where(Purchase.id == purchase_id)
    )
    purchase = db.scalar(stmt)
    if purchase is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase with id {purchase_id} was not found.",
        )
    return purchase


def create_purchase(db: Session, payload) -> Purchase:
    """Records a purchase and increases inventory as ONE logical operation.

    Everything below happens in a single transaction: the purchase header and
    its lines are written, every material's stock level is increased through a
    guarded SQL UPDATE and each movement gets a history row. The single
    `db.commit()` at the end means a failure anywhere (unknown supplier,
    unknown/inactive material…) rolls the whole thing back.
    """
    supplier = validate_supplier_exists(db, payload.supplier_id)

    requested_ids = [line.inventory_item_id for line in payload.items]
    material_rows = db.scalars(select(InventoryItem).where(InventoryItem.id.in_(requested_ids))).all()
    materials = {item.id: item for item in material_rows}

    missing = next((item_id for item_id in requested_ids if item_id not in materials), None)
    if missing is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Raw material with id {missing} was not found. It may have been removed.",
        )

    inactive = next((item.name for item in materials.values() if not item.is_active), None)
    if inactive is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'"{inactive}" is marked inactive and cannot be purchased.',
        )

    subtotal = 0.0
    lines = []
    for line in payload.items:
        material = materials[line.inventory_item_id]
        quantity = line.quantity
        unit_cost = line.unit_cost
        line_total = compute_line_total(quantity, unit_cost)
        subtotal += line_total
        lines.append(
            {
                "inventory_item_id": material.id,
                "item_name": material.name,
                "unit": material.unit,
                "quantity": quantity,
                "unit_cost": unit_cost,
                "line_total": line_total,
            }
        )
    subtotal = _round(subtotal)

    purchase = Purchase(
        purchase_number="PENDING",  # replaced after flush knows the id
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        purchase_date=payload.purchase_date or date.today(),
        subtotal=subtotal,
        total=subtotal,
        payment_status=payload.payment_status,
        notes=payload.notes,
    )
    for line in lines:
        purchase.items.append(PurchaseItem(**line))

    db.add(purchase)
    db.flush()  # assigns purchase.id (and therefore the number)

    purchase.purchase_number = f"PUR-{purchase.id:04d}"

    # Stock In per material — same session, same transaction as the purchase.
    for line in lines:
        material = materials[line["inventory_item_id"]]
        new_balance = material.current_quantity + line["quantity"]
        db.execute(
            update(InventoryItem)
            .where(InventoryItem.id == material.id)
            .values(current_quantity=InventoryItem.current_quantity + line["quantity"])
        )
        db.add(
            InventoryTransaction(
                item_id=material.id,
                transaction_type="Stock In",
                quantity=line["quantity"],
                balance_after=new_balance,
                note=f"Purchase {purchase.purchase_number}",
            )
        )

    db.commit()  # the one commit — purchase + stock + history all-or-nothing
    return get_purchase_or_404(db, purchase.id)


def update_payment_status(db: Session, purchase_id: int, new_status: str) -> Purchase:
    purchase = get_purchase_or_404(db, purchase_id)
    purchase.payment_status = new_status
    db.commit()
    return get_purchase_or_404(db, purchase_id)
