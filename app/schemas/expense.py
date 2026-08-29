from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.expense import EXPENSE_CATEGORIES, PAYMENT_METHODS


def round_amount(value: float) -> float:
    return round(value, 2)


class ExpenseBase(BaseModel):
    """Shared fields and rules for creating/updating an expense record.

    `title` may repeat (e.g. two electricity bills) — there is deliberately no
    uniqueness rule. `category` must be one of the cafe's configured list
    (Electricity, Gas, Rent, Maintenance, Cleaning, Internet, Miscellaneous).
    """

    title: str = Field(min_length=1, max_length=120)
    category: str
    amount: float = Field(ge=0, le=99999999)
    expense_date: date | None = None
    payment_method: str = "Cash"
    notes: str | None = Field(default=None, max_length=255)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value):
        value = (value or "").strip()
        if not value:
            raise ValueError("Expense title is required.")
        return value

    @field_validator("amount", mode="before")
    @classmethod
    def reject_boolean_and_negatives(cls, value):
        if isinstance(value, bool):
            raise ValueError("Value must be a number.")
        return value

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, value):
        if value <= 0:
            raise ValueError("Expense amount must be greater than zero.")
        return round_amount(value)

    @field_validator("category")
    @classmethod
    def category_in_allowed_list(cls, value):
        value = (value or "").strip()
        if value not in EXPENSE_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(EXPENSE_CATEGORIES)}.")
        return value

    @field_validator("payment_method")
    @classmethod
    def payment_method_in_allowed_list(cls, value):
        value = (value or "").strip()
        if value not in PAYMENT_METHODS:
            raise ValueError(f"Payment method must be one of: {', '.join(PAYMENT_METHODS)}.")
        return value

    @field_validator("notes", mode="before")
    @classmethod
    def strip_notes(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class ExpenseCreate(ExpenseBase):
    """Request body for creating an expense record."""


class ExpenseUpdate(ExpenseBase):
    """Request body for replacing an expense record (full update via PUT)."""


class ExpenseRead(BaseModel):
    """Expense returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    amount: float
    expense_date: date | None
    payment_method: str
    notes: str | None
    created_at: datetime
    updated_at: datetime | None
