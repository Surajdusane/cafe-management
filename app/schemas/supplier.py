import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
PHONE_PATTERN = re.compile(r"^[6-9]\d{9}$")


class SupplierBase(BaseModel):
    """Shared fields and rules for creating/updating a supplier."""

    name: str = Field(min_length=1, max_length=100)
    contact_person: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=15)
    email: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    materials_supplied: str | None = Field(default=None, max_length=255)
    is_active: bool = True

    @field_validator(
        "name",
        "contact_person",
        "phone",
        "email",
        "address",
        "materials_supplied",
        mode="before",
    )
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
            raise ValueError("Supplier name is required.")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if value is not None and not PHONE_PATTERN.fullmatch(value):
            raise ValueError("Enter a valid 10-digit mobile number.")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if value is not None and not EMAIL_PATTERN.fullmatch(value.lower()):
            raise ValueError("Enter a valid email address.")
        return value.lower() if value else value


class SupplierCreate(SupplierBase):
    """Request body for creating a supplier."""


class SupplierUpdate(SupplierBase):
    """Request body for replacing a supplier (full update via PUT)."""


class SupplierBrief(BaseModel):
    """Lightweight supplier info embedded inside an inventory item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool


class SupplierRead(BaseModel):
    """Supplier returned by the API. inventory_item_count is filled by the service."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    contact_person: str | None
    phone: str | None
    email: str | None
    address: str | None
    materials_supplied: str | None
    is_active: bool
    inventory_item_count: int = 0
    created_at: datetime
    updated_at: datetime | None
