from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.menu_item import MenuItem


def _raise_duplicate(db: Session, name: str, exclude_id: int | None = None) -> None:
    """Raise 409 when another category already uses the same name (case-insensitive)."""
    stmt = select(Category).where(func.lower(Category.name) == name.lower())
    if exclude_id is not None:
        stmt = stmt.where(Category.id != exclude_id)
    existing = db.scalar(stmt)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'A category named "{existing.name}" already exists.',
        )


def list_categories(
    db: Session,
    search: str | None = None,
    include_inactive: bool = True,
) -> list[Category]:
    """Return categories ordered by name, with a live item count on each row."""
    conditions = []
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(Category.name.ilike(term), Category.description.ilike(term)))
    if not include_inactive:
        conditions.append(Category.is_active.is_(True))

    item_count = (
        select(func.count(MenuItem.id))
        .where(MenuItem.category_id == Category.id)
        .correlate(Category)
        .scalar_subquery()
    )

    stmt = select(Category, item_count.label("item_count"))
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.order_by(Category.name)

    categories: list[Category] = []
    for category, count in db.execute(stmt).all():
        category.item_count = count
        categories.append(category)
    return categories


def get_category_or_404(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} was not found.",
        )
    category.item_count = len(category.items)
    return category


def create_category(db: Session, payload) -> Category:
    _raise_duplicate(db, payload.name)
    category = Category(**payload.model_dump())
    category.item_count = 0
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, payload) -> Category:
    category = get_category_or_404(db, category_id)
    _raise_duplicate(db, payload.name, exclude_id=category_id)

    for field, value in payload.model_dump().items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)

    category.item_count = len(category.items)
    return category


def delete_category(db: Session, category_id: int) -> int:
    """Delete an empty category. Returns how many items it held if it is not empty."""
    category = get_category_or_404(db, category_id)
    item_count = len(category.items)
    if item_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f'Cannot delete "{category.name}": {item_count} menu item(s) still use it. '
                "Move or delete its items first."
            ),
        )
    db.delete(category)
    db.commit()
    return item_count
