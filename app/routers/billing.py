from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order import OrderDetailRead, OrderSummaryRead, PaymentCreate
from app.services import billing_service

router = APIRouter(prefix="/api/bills", tags=["Billing"])


def _summary(order) -> dict:
    body = OrderSummaryRead.model_validate(order).model_dump(mode="json")
    body["item_count"] = len(order.items)
    return body


def _detail(order) -> dict:
    return OrderDetailRead.model_validate(order).model_dump(mode="json")


@router.get("")
def list_bills(
    search: str | None = Query(default=None, max_length=20),
    payment_status: str | None = Query(default=None),
    payment_method: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Bill list (orders with money focus) plus collection totals for the cards."""
    orders, summary = billing_service.list_bills(
        db,
        payment_status=payment_status,
        payment_method=payment_method,
        search=search,
    )
    data = {"items": [_summary(o) for o in orders], "count": len(orders), "summary": summary}
    return {"success": True, "data": data}


@router.get("/{order_id}")
def read_bill(order_id: int, db: Session = Depends(get_db)) -> dict:
    """Full bill detail including cafe branding for the printable receipt."""
    order = billing_service.get_bill_or_404(db, order_id)
    data = {
        "bill": OrderDetailRead.model_validate(order).model_dump(mode="json"),
        "cafe": billing_service.bill_summary_for_receipt(db),
    }
    return {"success": True, "data": data}


@router.post("/{order_id}/pay")
def pay_bill(order_id: int, payload: PaymentCreate, db: Session = Depends(get_db)) -> dict:
    """Records a payment against the order's bill."""
    order = billing_service.pay_bill(db, order_id, payload.payment_method)
    return {
        "success": True,
        "data": _detail(order),
        "message": f"Payment of method {payload.payment_method} recorded.",
    }
