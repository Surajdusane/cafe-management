from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.menu_item import MenuItemCreate, MenuItemRead, MenuItemUpdate
from app.services import menu_item_service

router = APIRouter(prefix="/api/menu/items", tags=["Menu Items"])


def _serialize(item) -> dict:
    return MenuItemRead.model_validate(item).model_dump(mode="json")


@router.get("")
def list_menu_items(
    search: str | None = Query(default=None, max_length=120),
    category_id: int | None = Query(default=None, gt=0),
    available_only: bool | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """List menu items with optional search, category and availability filters."""
    items = menu_item_service.list_menu_items(
        db,
        search=search,
        category_id=category_id,
        available_only=available_only,
    )
    data = {"items": [_serialize(i) for i in items], "count": len(items)}
    return {"success": True, "data": data}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_menu_item(payload: MenuItemCreate, db: Session = Depends(get_db)) -> dict:
    item = menu_item_service.create_menu_item(db, payload)
    return {"success": True, "data": _serialize(item), "message": "Menu item created."}


@router.get("/{item_id}")
def read_menu_item(item_id: int, db: Session = Depends(get_db)) -> dict:
    item = menu_item_service.get_item_or_404(db, item_id)
    return {"success": True, "data": _serialize(item)}


@router.put("/{item_id}")
def update_menu_item(
    item_id: int,
    payload: MenuItemUpdate,
    db: Session = Depends(get_db),
) -> dict:
    item = menu_item_service.update_menu_item(db, item_id, payload)
    return {"success": True, "data": _serialize(item), "message": "Menu item updated."}


@router.delete("/{item_id}")
def delete_menu_item(item_id: int, db: Session = Depends(get_db)) -> dict:
    menu_item_service.delete_menu_item(db, item_id)
    return {"success": True, "data": None, "message": "Menu item deleted."}
