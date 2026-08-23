from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.menu_item import MenuItem
from app.models.order import Order, OrderItem
from app.services.settings_service import get_or_create_settings


def _round(value: float) -> float:
    return round(value, 2)


def compute_totals(subtotal: float, discount_amount: float, tax_percent: float) -> dict:
    """The single money formula of the whole system:

        taxable = subtotal - discount
        tax     = taxable * tax_percent / 100
        total   = taxable + tax

    Kept as a pure function so it can be unit-tested without a database.
    """
    taxable = subtotal - discount_amount
    tax_amount = taxable * tax_percent / 100
    return {
        "subtotal": _round(subtotal),
        "tax_amount": _round(tax_amount),
        "total": _round(taxable + tax_amount),
    }


def list_orders(
    db: Session,
    status_filter: str | None = None,
    order_type: str | None = None,
    payment_status: str | None = None,
    search: str | None = None,
) -> list[Order]:
    stmt = select(Order).options(selectinload(Order.items))
    conditions = []
    if status_filter:
        conditions.append(Order.status == status_filter)
    if order_type:
        conditions.append(Order.order_type == order_type)
    if payment_status:
        conditions.append(Order.payment_status == payment_status)
    if search:
        conditions.append(Order.order_number.ilike(f"%{search.strip()}%"))
    if conditions:
        stmt = stmt.where(*conditions)
    # Newest first — staff care about the latest orders.
    stmt = stmt.order_by(Order.created_at.desc(), Order.id.desc())
    return list(db.scalars(stmt))


def get_order_or_404(db: Session, order_id: int) -> Order:
    stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    order = db.scalar(stmt)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} was not found.",
        )
    return order


def create_order(db: Session, payload) -> Order:
    """Validate menu items against the live menu, snapshot names/prices,
    calculate all money server-side and persist the order atomically."""
    requested_ids = [line.menu_item_id for line in payload.items]
    menu_rows = db.scalars(select(MenuItem).where(MenuItem.id.in_(requested_ids))).all()
    menu_items = {item.id: item for item in menu_rows}

    missing = next((item_id for item_id in requested_ids if item_id not in menu_items), None)
    if missing is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Menu item with id {missing} was not found. It may have been removed.",
        )

    unavailable = next((item.name for item in menu_items.values() if not item.is_available), None)
    if unavailable is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'"{unavailable}" is currently marked unavailable and cannot be ordered.',
        )

    subtotal = 0.0
    lines = []
    for line in payload.items:
        menu_item = menu_items[line.menu_item_id]
        unit_price = _round(menu_item.price)
        line_total = _round(unit_price * line.quantity)
        subtotal += line_total
        lines.append(
            {
                "menu_item_id": menu_item.id,
                "item_name": menu_item.name,
                "unit_price": unit_price,
                "quantity": line.quantity,
                "line_total": line_total,
            }
        )
    subtotal = _round(subtotal)

    if payload.discount_amount > subtotal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discount cannot be greater than the order subtotal.",
        )

    settings = get_or_create_settings(db)  # tax % snapshot comes from here
    totals = compute_totals(subtotal, payload.discount_amount, settings.tax_percent)

    order = Order(
        order_number="PENDING",  # replaced by the real number after flush knows the id
        order_type=payload.order_type,
        table_number=payload.table_number,
        status="Pending",
        subtotal=totals["subtotal"],
        discount_amount=payload.discount_amount,
        tax_percent=settings.tax_percent,
        tax_amount=totals["tax_amount"],
        total=totals["total"],
    )
    for line in lines:
        order.items.append(OrderItem(**line))

    db.add(order)
    db.flush()  # assigns order.id
    order.order_number = f"ORD-{order.id:04d}"
    db.commit()
    db.refresh(order)
    return get_order_or_404(db, order.id)


def update_order_status(db: Session, order_id: int, new_status: str) -> Order:
    order = get_order_or_404(db, order_id)
    if order.status == "Cancelled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cancelled orders cannot be changed. Create a new order instead.",
        )
    if new_status == "Cancelled" and order.payment_status == "Paid":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Paid orders cannot be cancelled. Handle the refund manually first.",
        )
    order.status = new_status
    db.commit()
    db.refresh(order)
    return get_order_or_404(db, order_id)


def delete_cancelled_order(db: Session, order_id: int) -> None:
    """Only cancelled orders may be removed; completed history stays intact."""
    order = get_order_or_404(db, order_id)
    if order.status != "Cancelled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Only "Cancelled" orders can be deleted. Cancel it first.',
        )
    db.delete(order)
    db.commit()
