from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.schemas.public_menu import PublicCafeBranding, PublicCategory, PublicMenuItem
from app.services.settings_service import get_or_create_settings


def _category_has_items(category: Category) -> bool:
    """A category section is only worth showing when it has at least one item."""
    return len(category.items) > 0


def get_public_menu(db: Session) -> dict:
    """Compose everything the public menu page needs in a single response.

    Customers receive only display data: active categories (with at least one item),
    every item including sold-out ones so availability can be shown honestly,
    plus the cafe branding from settings.
    """
    settings = get_or_create_settings(db)
    branding = PublicCafeBranding(
        name=settings.cafe_name,
        address=settings.address,
        phone=settings.phone,
        email=settings.email,
        logo_url=settings.logo_url,
        currency=settings.currency,
    )

    stmt = (
        select(Category)
        .where(Category.is_active.is_(True))
        .options(selectinload(Category.items))
        .order_by(Category.name)
    )
    categories = [
        PublicCategory(
            name=category.name,
            description=category.description,
            items=[
                PublicMenuItem.model_validate(item)
                for item in sorted(category.items, key=lambda i: i.name.lower())
            ],
        )
        for category in db.scalars(stmt)
        if _category_has_items(category)
    ]

    return {"cafe": branding.model_dump(mode="json"), "categories": [c.model_dump(mode="json") for c in categories]}
