from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.category import CategoryBrief, CategoryRead


def round_price(value: float) -> float:
    return round(value, 2)


class MenuItemBase(BaseModel):
    """Shared fields and rules for creating/updating a menu item."""

    category_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(gt=0, le=999999)
    image_url: str | None = Field(default=None, max_length=300)
    is_vegetarian: bool = True
    is_popular: bool = False
    is_available: bool = True

    @field_validator("category_id", "price", mode="before")
    @classmethod
    def reject_boolean_numbers(cls, value):
        # bool is a subclass of int; True/False must not pass as 1/0 prices or ids.
        if isinstance(value, bool):
            raise ValueError("Value must be a number.")
        return value

    @field_validator("name", "description", "image_url", mode="before")
    @classmethod
    def strip_and_empty_to_none(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip()
        return value or None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value):
        if not value:
            raise ValueError("Item name is required.")
        return value

    @field_validator("price")
    @classmethod
    def price_positive_and_rounded(cls, value):
        if value <= 0:
            raise ValueError("Price must be greater than zero.")
        return round_price(value)


class MenuItemCreate(MenuItemBase):
    """Request body for creating a menu item."""


class MenuItemUpdate(MenuItemBase):
    """Request body for replacing a menu item (full update via PUT)."""


class MenuItemRead(BaseModel):
    """Menu item returned by the API, including its category summary."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    description: str | None
    price: float
    image_url: str | None
    is_vegetarian: bool
    is_popular: bool
    is_available: bool
    created_at: datetime
    updated_at: datetime | None
    category: CategoryBrief | None = None
