from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.models.menu_item import MenuItem


def _raise_duplicate(db: Session, category_id: int, name: str, exclude_id: int | None = None) -> None:
    """Raise 409 when the same category already has an item with this name (case-insensitive)."""
    stmt = select(MenuItem).where(
        MenuItem.category_id == category_id,
        func.lower(MenuItem.name) == name.lower(),
    )
    if exclude_id is not None:
        stmt = stmt.where(MenuItem.id != exclude_id)
    existing = db.scalar(stmt)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'"{existing.name}" already exists in this category.',
        )


def _validate_category_exists(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} was not found. Create it first.",
        )
    return category


def list_menu_items(
    db: Session,
    search: str | None = None,
    category_id: int | None = None,
    available_only: bool | None = None,
) -> list[MenuItem]:
    conditions = []
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(MenuItem.name.ilike(term), MenuItem.description.ilike(term)))
    if category_id is not None:
        conditions.append(MenuItem.category_id == category_id)
    if available_only is True:
        conditions.append(MenuItem.is_available.is_(True))

    stmt = select(MenuItem).options(selectinload(MenuItem.category))
    if conditions:
        stmt = stmt.where(*conditions)
    # Newest first would fight "menu order"; alphabetical by name is predictable for staff.
    stmt = stmt.order_by(MenuItem.name)

    return list(db.scalars(stmt))


def get_item_or_404(db: Session, item_id: int) -> MenuItem:
    stmt = select(MenuItem).options(selectinload(MenuItem.category)).where(MenuItem.id == item_id)
    item = db.scalar(stmt)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Menu item with id {item_id} was not found.",
        )
    return item


def create_menu_item(db: Session, payload) -> MenuItem:
    _validate_category_exists(db, payload.category_id)
    _raise_duplicate(db, payload.category_id, payload.name)

    item = MenuItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return get_item_or_404(db, item.id)


def update_menu_item(db: Session, item_id: int, payload) -> MenuItem:
    item = get_item_or_404(db, item_id)
    _validate_category_exists(db, payload.category_id)
    _raise_duplicate(db, payload.category_id, payload.name, exclude_id=item_id)

    for field, value in payload.model_dump().items():
        setattr(item, field, value)
    db.commit()
    return get_item_or_404(db, item_id)


def delete_menu_item(db: Session, item_id: int) -> str:
    item = get_item_or_404(db, item_id)
    name = item.name
    db.delete(item)
    db.commit()
    return name
