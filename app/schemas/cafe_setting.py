import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
PHONE_PATTERN = re.compile(r"^[6-9]\d{9}$")


class CafeSettingUpdate(BaseModel):
    """Request body for updating cafe settings (full replace via PUT)."""

    cafe_name: str = Field(min_length=1, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=10)
    email: str | None = Field(default=None, max_length=100)
    logo_url: str | None = Field(default=None, max_length=300)
    tax_percent: float = Field(ge=0, le=100)
    currency: str = Field(min_length=1, max_length=8)
    receipt_footer: str | None = Field(default=None, max_length=200)

    @field_validator(
        "cafe_name",
        "address",
        "phone",
        "email",
        "logo_url",
        "currency",
        "receipt_footer",
        mode="before",
    )
    @classmethod
    def strip_and_empty_to_none(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip()
        return value or None

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


class CafeSettingRead(BaseModel):
    """Settings returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cafe_name: str
    address: str | None
    phone: str | None
    email: str | None
    logo_url: str | None
    tax_percent: float
    currency: str
    receipt_footer: str | None
    updated_at: datetime | None
