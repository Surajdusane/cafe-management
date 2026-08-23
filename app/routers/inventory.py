from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemDetailRead,
    InventoryItemSummaryRead,
    InventoryItemUpdate,
    StockTransactionCreate,
    StockTransactionRead,
)
from app.services import inventory_service

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


def _serialize_summary(item) -> dict:
    body = InventoryItemSummaryRead.model_validate(item).model_dump(mode="json")
    body["is_low_stock"] = item.is_low_stock
    return body


def _serialize_detail(item) -> dict:
    body = _serialize_summary(item)
    body["transactions"] = [
        StockTransactionRead.model_validate(t).model_dump(mode="json")
        for t in item.transactions[:20]  # newest first (relationship is ordered desc)
    ]
    return body


@router.get("/items")
def list_items(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    supplier_id: int | None = Query(default=None, gt=0),
    low_stock_only: bool = False,
    include_inactive: bool = True,
    db: Session = Depends(get_db),
) -> dict:
    """List raw materials with stock levels, supplier and low-stock flags."""
    items = inventory_service.list_items(
        db,
        search=search,
        category=category,
        supplier_id=supplier_id,
        low_stock_only=low_stock_only,
        include_inactive=include_inactive,
    )
    data = {"items": [_serialize_summary(i) for i in items], "count": len(items)}
    data["summary"] = inventory_service.get_summary(db)
    return {"success": True, "data": data}


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)) -> dict:
    """Distinct material categories for the filter dropdown."""
    categories = inventory_service.list_categories(db)
    return {"success": True, "data": {"categories": categories}}


@router.get("/transactions")
def list_transactions(
    item_id: int | None = Query(default=None, gt=0),
    transaction_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    """Global movement history, newest first."""
    transactions = inventory_service.list_transactions(
        db, item_id=item_id, transaction_type=transaction_type, limit=limit
    )
    data = {"items": transactions, "count": len(transactions)}
    return {"success": True, "data": data}


@router.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(payload: InventoryItemCreate, db: Session = Depends(get_db)) -> dict:
    """Creates a raw material. A non-zero opening quantity automatically writes
    the first 'Stock In' history row ('Opening stock')."""
    item = inventory_service.create_item(db, payload)
    return {
        "success": True,
        "data": _serialize_detail(item),
        "message": "Raw material created.",
    }


@router.get("/items/{item_id}")
def read_item(item_id: int, db: Session = Depends(get_db)) -> dict:
    item = inventory_service.get_item_or_404(db, item_id, with_transactions=True)
    return {"success": True, "data": _serialize_detail(item)}


@router.put("/items/{item_id}")
def update_item(item_id: int, payload: InventoryItemUpdate, db: Session = Depends(get_db)) -> dict:
    """Replaces descriptive fields. Stock level changes only via movements."""
    item = inventory_service.update_item(db, item_id, payload)
    return {"success": True, "data": _serialize_detail(item), "message": "Raw material updated."}


@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)) -> dict:
    name = inventory_service.delete_item(db, item_id)
    return {"success": True, "data": None, "message": f"Raw material '{name}' deleted."}


@router.post("/items/{item_id}/stock")
def record_stock_movement(
    item_id: int,
    payload: StockTransactionCreate,
    db: Session = Depends(get_db),
) -> dict:
    """Records Stock In / Stock Out / Adjustment atomically and returns the
    updated level plus the written history row."""
    item, transaction = inventory_service.record_transaction(db, item_id, payload)
    verb = {
        "Stock In": "added to",
        "Stock Out": "removed from",
        "Adjustment": "adjusted for",
    }[payload.transaction_type]
    return {
        "success": True,
        "data": {
            "item": _serialize_summary(item),
            "transaction": StockTransactionRead.model_validate(transaction).model_dump(mode="json"),
        },
        "message": (
            f"{payload.quantity} {item.unit} {verb} '{item.name}'. "
            f"New balance: {round(item.current_quantity, 3)} {item.unit}."
        ),
    }
