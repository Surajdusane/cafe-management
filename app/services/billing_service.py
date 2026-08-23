from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order
from app.services import order_service


def list_bills(
    db: Session,
    payment_status: str | None = None,
    payment_method: str | None = None,
    search: str | None = None,
) -> tuple[list[Order], dict]:
    """Bills are orders seen through a money lens. Returns the rows plus a
    small totals summary for the billing dashboard cards."""
    orders = order_service.list_orders(db, payment_status=payment_status, search=search)
    if payment_method:
        orders = [order for order in orders if order.payment_method == payment_method]

    billed = round(sum(order.total for order in orders), 2)
    collected = round(sum(o.total for o in orders if o.payment_status == "Paid"), 2)
    summary = {
        "count": len(orders),
        "billed_total": billed,
        "collected_total": collected,
        "outstanding_total": round(billed - collected, 2),
    }
    return orders, summary


def get_bill_or_404(db: Session, order_id: int) -> Order:
    return order_service.get_order_or_404(db, order_id)


def pay_bill(db: Session, order_id: int, payment_method: str) -> Order:
    """Record a payment. The server decides 'Paid' — the client cannot send it."""
    order = get_bill_or_404(db, order_id)
    if order.payment_status == "Paid":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bill {order.order_number} is already paid.",
        )
    if order.status == "Cancelled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cancelled orders cannot be paid.",
        )
    order.payment_method = payment_method
    order.payment_status = "Paid"
    order.paid_at = func.now()
    db.commit()
    db.refresh(order)
    return order_service.get_order_or_404(db, order_id)


def bill_summary_for_receipt(db: Session) -> dict:
    """Cafe branding + tax info printed on top of every receipt."""
    from app.services.settings_service import get_or_create_settings

    settings = get_or_create_settings(db)
    return {
        "cafe_name": settings.cafe_name,
        "address": settings.address,
        "phone": settings.phone,
        "logo_url": settings.logo_url,
        "currency": settings.currency,
        "receipt_footer": settings.receipt_footer,
    }
