from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services import category_service

router = APIRouter(prefix="/api/categories", tags=["Categories"])


def _serialize(category) -> dict:
    return CategoryRead.model_validate(category).model_dump(mode="json")


@router.get("")
def list_categories(
    search: str | None = Query(default=None, max_length=80),
    include_inactive: bool = True,
    db: Session = Depends(get_db),
) -> dict:
    """List categories (newest last), each with a live menu-item count."""
    categories = category_service.list_categories(db, search=search, include_inactive=include_inactive)
    data = {"items": [_serialize(c) for c in categories], "count": len(categories)}
    return {"success": True, "data": data}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> dict:
    category = category_service.create_category(db, payload)
    return {"success": True, "data": _serialize(category), "message": "Category created."}


@router.get("/{category_id}")
def read_category(category_id: int, db: Session = Depends(get_db)) -> dict:
    category = category_service.get_category_or_404(db, category_id)
    return {"success": True, "data": _serialize(category)}


@router.put("/{category_id}")
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
) -> dict:
    category = category_service.update_category(db, category_id, payload)
    return {"success": True, "data": _serialize(category), "message": "Category updated."}


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)) -> dict:
    category_service.delete_category(db, category_id)
    return {"success": True, "data": None, "message": "Category deleted."}
