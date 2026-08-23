from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ORDER_TYPES = ["Dine-in", "Takeaway"]
ORDER_STATUSES = ["Pending", "Preparing", "Ready", "Completed", "Cancelled"]
PAYMENT_METHODS = ["Cash", "UPI", "Card", "Other"]
PAYMENT_STATUSES = ["Unpaid", "Paid"]

MAX_QUANTITY = 999
MAX_ITEMS_PER_ORDER = 50
MAX_TABLE_NUMBER = 999


def round_money(value: float) -> float:
    return round(value, 2)


class OrderItemCreate(BaseModel):
    """One requested line: which menu item and how many units."""

    menu_item_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=MAX_QUANTITY)

    @field_validator("menu_item_id", "quantity", mode="before")
    @classmethod
    def reject_boolean_numbers(cls, value):
        # bool is a subclass of int; True must not pass as a quantity or id.
        if isinstance(value, bool):
            raise ValueError("Value must be a number.")
        return value


class OrderCreate(BaseModel):
    """Request body for creating an order. Totals are calculated by the server,
    so the client never sends prices or amounts other than the discount."""

    order_type: Literal["Dine-in", "Takeaway"]
    table_number: int | None = Field(default=None, ge=1, le=MAX_TABLE_NUMBER)
    items: list[OrderItemCreate] = Field(min_length=1, max_length=MAX_ITEMS_PER_ORDER)
    discount_amount: float = Field(default=0.0, ge=0, le=999999)

    @field_validator("discount_amount", mode="before")
    @classmethod
    def reject_boolean_discount(cls, value):
        if isinstance(value, bool):
            raise ValueError("Value must be a number.")
        return value

    @field_validator("discount_amount")
    @classmethod
    def round_discount(cls, value):
        return round_money(value)

    @model_validator(mode="after")
    def apply_order_type_rules(self):
        if self.order_type == "Dine-in" and self.table_number is None:
            raise ValueError("Table number is required for dine-in orders.")
        if self.order_type == "Takeaway":
            self.table_number = None  # a takeaway never sits at a table

        item_ids = [line.menu_item_id for line in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("Each menu item may appear only once; increase its quantity instead.")
        return self


class OrderStatusUpdate(BaseModel):
    """Request body for moving an order through its workflow."""

    status: Literal["Pending", "Preparing", "Ready", "Completed", "Cancelled"]


class PaymentCreate(BaseModel):
    """Request body for recording a bill payment."""

    payment_method: Literal["Cash", "UPI", "Card", "Other"]


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    menu_item_id: int | None
    item_name: str
    unit_price: float
    quantity: int
    line_total: float


class OrderSummaryRead(BaseModel):
    """Order row for lists (orders page and billing table)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    order_type: str
    table_number: int | None
    status: str
    item_count: int = 0
    subtotal: float
    discount_amount: float
    tax_percent: float
    tax_amount: float
    total: float
    payment_method: str | None
    payment_status: str
    created_at: datetime


class OrderDetailRead(OrderSummaryRead):
    """Full order including its item lines and audit timestamps."""

    paid_at: datetime | None
    updated_at: datetime | None
    items: list[OrderItemRead] = []
