from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.purchase import (
    PaymentStatusUpdate,
    PurchaseCreate,
    PurchaseDetailRead,
    PurchaseSummaryRead,
)
from app.services import purchase_service

router = APIRouter(prefix="/api/purchases", tags=["Purchases"])


def _summary(purchase) -> dict:
    body = PurchaseSummaryRead.model_validate(purchase).model_dump(mode="json")
    body["item_count"] = len(purchase.items)
    return body


def _detail(purchase) -> dict:
    body = PurchaseDetailRead.model_validate(purchase).model_dump(mode="json")
    body["item_count"] = len(purchase.items)
    return body


@router.get("")
def list_purchases(
    search: str | None = Query(default=None, max_length=120),
    supplier_id: int | None = Query(default=None, gt=0),
    payment_status: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Purchase history newest first with search, supplier, payment and date
    filters. `summary` carries totals for the page's stat cards."""
    purchases = purchase_service.list_purchases(
        db,
        search=search,
        supplier_id=supplier_id,
        payment_status=payment_status,
        start_date=start_date,
        end_date=end_date,
    )
    data = {
        "items": [_summary(p) for p in purchases],
        "count": len(purchases),
        "summary": purchase_service.summarize(purchases),
    }
    return {"success": True, "data": data}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_purchase(payload: PurchaseCreate, db: Session = Depends(get_db)) -> dict:
    """Records a purchase. The server validates the supplier and materials,
    calculates all money values and increases inventory — all in one
    transaction, so a failed purchase never changes stock."""
    purchase = purchase_service.create_purchase(db, payload)
    return {
        "success": True,
        "data": _detail(purchase),
        "message": (
            f"Purchase {purchase.purchase_number} recorded. "
            f"Inventory updated for {len(purchase.items)} material(s)."
        ),
    }


@router.get("/{purchase_id}")
def read_purchase(purchase_id: int, db: Session = Depends(get_db)) -> dict:
    purchase = purchase_service.get_purchase_or_404(db, purchase_id)
    return {"success": True, "data": _detail(purchase)}


@router.put("/{purchase_id}/payment-status")
def change_payment_status(
    purchase_id: int,
    payload: PaymentStatusUpdate,
    db: Session = Depends(get_db),
) -> dict:
    """Marks a purchase Paid or reverts it to Unpaid."""
    purchase = purchase_service.update_payment_status(db, purchase_id, payload.payment_status)
    return {
        "success": True,
        "data": _detail(purchase),
        "message": f"{purchase.purchase_number} marked {payload.payment_status}.",
    }
