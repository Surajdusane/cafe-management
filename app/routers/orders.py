from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order import (
    OrderCreate,
    OrderDetailRead,
    OrderStatusUpdate,
    OrderSummaryRead,
)
from app.services import order_service

router = APIRouter(prefix="/api/orders", tags=["Orders"])


def _summary(order) -> dict:
    body = OrderSummaryRead.model_validate(order).model_dump(mode="json")
    body["item_count"] = len(order.items)
    return body


def _detail(order) -> dict:
    return OrderDetailRead.model_validate(order).model_dump(mode="json")


@router.get("")
def list_orders(
    search: str | None = Query(default=None, max_length=20),
    order_status: str | None = Query(default=None),
    order_type: str | None = Query(default=None),
    payment_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """List orders newest first with optional workflow filters."""
    orders = order_service.list_orders(
        db,
        status_filter=order_status,
        order_type=order_type,
        payment_status=payment_status,
        search=search,
    )
    data = {"items": [_summary(o) for o in orders], "count": len(orders)}
    return {"success": True, "data": data}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)) -> dict:
    """Creates an order. The server validates items, snapshots prices and
    calculates subtotal/tax/total — the client cannot send money values."""
    order = order_service.create_order(db, payload)
    return {"success": True, "data": _detail(order), "message": "Order created."}


@router.get("/{order_id}")
def read_order(order_id: int, db: Session = Depends(get_db)) -> dict:
    order = order_service.get_order_or_404(db, order_id)
    return {"success": True, "data": _detail(order)}


@router.put("/{order_id}/status")
def change_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
) -> dict:
    """Moves an order through Pending → Preparing → Ready → Completed (or Cancelled)."""
    order = order_service.update_order_status(db, order_id, payload.status)
    return {
        "success": True,
        "data": _detail(order),
        "message": f"Order marked as {payload.status}.",
    }


@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)) -> dict:
    """Hard-deletes an order — allowed only for cancelled ones."""
    order_service.delete_cancelled_order(db, order_id)
    return {"success": True, "data": None, "message": "Order deleted."}
