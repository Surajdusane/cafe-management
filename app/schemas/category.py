from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryBase(BaseModel):
    """Shared fields and rules for creating/updating a category."""

    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool = True

    @field_validator("name", "description", mode="before")
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
            raise ValueError("Category name is required.")
        return value


class CategoryCreate(CategoryBase):
    """Request body for creating a category."""


class CategoryUpdate(CategoryBase):
    """Request body for replacing a category (full update via PUT)."""


class CategoryRead(BaseModel):
    """Category returned by the API. item_count is filled in by the service."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    is_active: bool
    item_count: int = 0
    created_at: datetime
    updated_at: datetime | None


class CategoryBrief(BaseModel):
    """Lightweight category info embedded inside a menu item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool
