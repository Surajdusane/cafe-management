from fastapi import HTTPException, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.supplier import Supplier
from app.services.supplier_service import validate_supplier_exists


def _raise_duplicate(db: Session, name: str, exclude_id: int | None = None) -> None:
    """Raise 409 when another raw material already uses this name (case-insensitive)."""
    stmt = select(InventoryItem).where(func.lower(InventoryItem.name) == name.lower())
    if exclude_id is not None:
        stmt = stmt.where(InventoryItem.id != exclude_id)
    existing = db.scalar(stmt)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'A raw material named "{existing.name}" already exists.',
        )


def _transaction_count_stmt():
    return (
        select(func.count(InventoryTransaction.id))
        .where(InventoryTransaction.item_id == InventoryItem.id)
        .correlate(InventoryItem)
        .scalar_subquery()
    )


def list_items(
    db: Session,
    search: str | None = None,
    category: str | None = None,
    supplier_id: int | None = None,
    low_stock_only: bool = False,
    include_inactive: bool = True,
) -> list[InventoryItem]:
    conditions = []
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(InventoryItem.name.ilike(term), InventoryItem.category.ilike(term)))
    if category:
        conditions.append(InventoryItem.category == category.strip())
    if supplier_id is not None:
        conditions.append(InventoryItem.supplier_id == supplier_id)
    if low_stock_only:
        conditions.append(InventoryItem.current_quantity <= InventoryItem.minimum_stock)
    if not include_inactive:
        conditions.append(InventoryItem.is_active.is_(True))

    stmt = select(InventoryItem, _transaction_count_stmt().label("transaction_count"))
    stmt = stmt.options(selectinload(InventoryItem.supplier))
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.order_by(InventoryItem.name)

    items: list[InventoryItem] = []
    for item, count in db.execute(stmt).all():
        item.transaction_count = count
        items.append(item)
    return items


def list_categories(db: Session) -> list[str]:
    """Distinct material categories, used to fill the page filter dropdown."""
    rows = db.scalars(select(InventoryItem.category).distinct().order_by(InventoryItem.category))
    return [row for row in rows if row]


def get_item_or_404(
    db: Session,
    item_id: int,
    *,
    with_transactions: bool = False,
) -> InventoryItem:
    stmt = select(InventoryItem).options(selectinload(InventoryItem.supplier))
    if with_transactions:
        stmt = stmt.options(selectinload(InventoryItem.transactions))
    stmt = stmt.where(InventoryItem.id == item_id)

    item = db.scalar(stmt)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Raw material with id {item_id} was not found.",
        )
    item.transaction_count = len(item.transactions) if with_transactions else (
        db.scalar(
            select(func.count(InventoryTransaction.id)).where(InventoryTransaction.item_id == item_id)
        )
        or 0
    )
    return item


def create_item(db: Session, payload) -> InventoryItem:
    _raise_duplicate(db, payload.name)
    if payload.supplier_id is not None:
        validate_supplier_exists(db, payload.supplier_id)

    data = payload.model_dump()
    opening_quantity = data.pop("initial_quantity")
    item = InventoryItem(current_quantity=opening_quantity, **data)

    db.add(item)
    db.flush()  # assigns item.id so the opening movement can reference it

    if opening_quantity > 0:
        db.add(
            InventoryTransaction(
                item_id=item.id,
                transaction_type="Stock In",
                quantity=opening_quantity,
                balance_after=opening_quantity,
                note="Opening stock",
            )
        )
    db.commit()
    return get_item_or_404(db, item.id)


def update_item(db: Session, item_id: int, payload) -> InventoryItem:
    """Updates descriptive fields only. The stock level itself never changes
    here — that happens exclusively through stock movements."""
    item = get_item_or_404(db, item_id)
    _raise_duplicate(db, payload.name, exclude_id=item_id)
    if payload.supplier_id is not None:
        validate_supplier_exists(db, payload.supplier_id)

    for field, value in payload.model_dump().items():
        setattr(item, field, value)
    db.commit()
    return get_item_or_404(db, item_id)


def delete_item(db: Session, item_id: int) -> str:
    """Deletes a material together with its movement history (ORM cascade)."""
    item = get_item_or_404(db, item_id)
    name = item.name
    db.delete(item)
    db.commit()
    return name


def record_transaction(db: Session, item_id: int, payload) -> tuple[InventoryItem, InventoryTransaction]:
    """Applies one stock movement atomically and writes its history row.

    Atomicity: Stock Out uses a guarded SQL UPDATE (`WHERE current_quantity >= q`)
    so two simultaneous requests can never both remove the same units — the
    loser simply matches zero rows and gets a 409.
    """
    item = get_item_or_404(db, item_id)
    move_type = payload.transaction_type
    quantity = payload.quantity

    if move_type == "Stock In":
        stmt = update(InventoryItem).where(InventoryItem.id == item_id).values(
            current_quantity=InventoryItem.current_quantity + quantity
        )
        new_balance = item.current_quantity + quantity
    elif move_type == "Stock Out":
        stmt = (
            update(InventoryItem)
            .where(
                InventoryItem.id == item_id,
                InventoryItem.current_quantity >= quantity,
            )
            .values(current_quantity=InventoryItem.current_quantity - quantity)
        )
        new_balance = item.current_quantity - quantity
    else:  # Adjustment — set the level to the counted amount (>= 0 enforced by schema)
        stmt = (
            update(InventoryItem)
            .where(InventoryItem.id == item_id)
            .values(current_quantity=quantity)
        )
        new_balance = quantity

    result = db.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Not enough stock for '{item.name}': {item.current_quantity} {item.unit} "
                f"available but {quantity} {item.unit} requested."
            ),
        )

    transaction = InventoryTransaction(
        item_id=item_id,
        transaction_type=move_type,
        quantity=quantity,
        balance_after=new_balance,
        note=payload.note,
    )
    db.add(transaction)
    db.commit()

    db.refresh(item)
    return item, transaction


def list_transactions(
    db: Session,
    item_id: int | None = None,
    transaction_type: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Movement history, newest first, optionally filtered by item/type."""
    conditions = []
    if item_id is not None:
        conditions.append(InventoryTransaction.item_id == item_id)
    if transaction_type:
        conditions.append(InventoryTransaction.transaction_type == transaction_type)

    stmt = (
        select(InventoryTransaction, InventoryItem.name.label("item_name"))
        .join(InventoryItem, InventoryTransaction.item_id == InventoryItem.id)
        .order_by(InventoryTransaction.id.desc())
        .limit(limit)
    )
    if conditions:
        stmt = stmt.where(*conditions)

    history: list[dict] = []
    for transaction, item_name in db.execute(stmt).all():
        row = {
            "id": transaction.id,
            "item_id": transaction.item_id,
            "item_name": item_name,
            "transaction_type": transaction.transaction_type,
            "quantity": round(transaction.quantity, 3),
            "balance_after": round(transaction.balance_after, 3),
            "note": transaction.note,
            "created_at": transaction.created_at,
        }
        history.append(row)
    return history


def get_summary(db: Session) -> dict:
    total_items = db.scalar(select(func.count(InventoryItem.id))) or 0
    active_items = (
        db.scalar(select(func.count(InventoryItem.id)).where(InventoryItem.is_active.is_(True))) or 0
    )
    low_stock_items = (
        db.scalar(
            select(func.count(InventoryItem.id)).where(
                InventoryItem.current_quantity <= InventoryItem.minimum_stock
            )
        )
        or 0
    )
    total_suppliers = db.scalar(select(func.count(Supplier.id))) or 0
    return {
        "total_items": total_items,
        "active_items": active_items,
        "low_stock_items": low_stock_items,
        "total_suppliers": total_suppliers,
    }
