from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PAYMENT_STATUSES = ["Unpaid", "Paid"]

MAX_ITEMS_PER_PURCHASE = 50
MAX_QUANTITY = 999999


def round_money(value: float) -> float:
    return round(value, 2)


def round_quantity(value: float) -> float:
    return round(value, 3)


class PurchaseItemCreate(BaseModel):
    """One requested line: which raw material, how much and at what unit cost.

    The client sends the cost it agreed with the supplier; totals are still
    calculated by the server from these values.
    """

    inventory_item_id: int = Field(gt=0)
    quantity: float = Field(gt=0, le=MAX_QUANTITY)
    unit_cost: float = Field(ge=0, le=999999)

    @field_validator("inventory_item_id", "quantity", "unit_cost", mode="before")
    @classmethod
    def reject_boolean_numbers(cls, value):
        # bool is a subclass of int/float; True must not pass as a number.
        if isinstance(value, bool):
            raise ValueError("Value must be a number.")
        return value

    @field_validator("quantity")
    @classmethod
    def round_quantity_value(cls, value):
        return round_quantity(value)

    @field_validator("unit_cost")
    @classmethod
    def round_unit_cost(cls, value):
        return round_money(value)


class PurchaseCreate(BaseModel):
    """Request body for recording a purchase. The server validates the
    supplier/materials, calculates all money values and increases inventory
    in one atomic step. `purchase_date` defaults to today when omitted."""

    supplier_id: int = Field(gt=0)
    purchase_date: date | None = None
    payment_status: Literal["Unpaid", "Paid"] = "Unpaid"
    items: list[PurchaseItemCreate] = Field(min_length=1, max_length=MAX_ITEMS_PER_PURCHASE)
    notes: str | None = Field(default=None, max_length=255)

    @field_validator("supplier_id", mode="before")
    @classmethod
    def reject_boolean_id(cls, value):
        # bool is a subclass of int; True must not sneak in as supplier 1.
        if isinstance(value, bool):
            raise ValueError("Value must be a number.")
        return value

    @field_validator("notes", mode="before")
    @classmethod
    def strip_and_empty_to_none(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def reject_duplicate_materials(self):
        item_ids = [line.inventory_item_id for line in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError(
                "Each raw material may appear only once; increase its quantity instead."
            )
        return self


class PaymentStatusUpdate(BaseModel):
    """Request body for marking a purchase paid or unpaid."""

    payment_status: Literal["Unpaid", "Paid"]


class PurchaseItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inventory_item_id: int | None
    item_name: str
    unit: str
    quantity: float
    unit_cost: float
    line_total: float


class PurchaseSummaryRead(BaseModel):
    """Purchase row for lists (item_count is filled from the loaded lines)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_number: str
    supplier_id: int | None
    supplier_name: str
    purchase_date: date
    subtotal: float
    total: float
    payment_status: str
    notes: str | None
    created_at: datetime
    item_count: int = 0


class PurchaseDetailRead(PurchaseSummaryRead):
    """Full purchase including its material lines and audit timestamps."""

    updated_at: datetime | None
    items: list[PurchaseItemRead] = []


class PurchaseSummary(BaseModel):
    """Totals for the purchases page stat cards over the filtered result set."""

    count: int
    total_amount: float
    unpaid_count: int
    unpaid_amount: float
