from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.supplier import SupplierBrief


def round_stock(value: float) -> float:
    return round(value, 3)


class InventoryItemBase(BaseModel):
    """Shared fields and rules for creating/updating a raw material."""

    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    unit: Literal["Kg", "Gram", "Litre", "Millilitre", "Piece", "Packet", "Box"]
    minimum_stock: float = Field(default=0.0, ge=0, le=999999)
    purchase_price: float = Field(default=0.0, ge=0, le=999999)
    supplier_id: int | None = Field(default=None, gt=0)
    is_active: bool = True
    notes: str | None = Field(default=None, max_length=255)

    @field_validator("supplier_id", "minimum_stock", "purchase_price", mode="before")
    @classmethod
    def reject_boolean_numbers(cls, value):
        # bool is a subclass of int; True/False must not pass as 1/0 numbers.
        if isinstance(value, bool):
            raise ValueError("Value must be a number.")
        return value

    @field_validator("name", "category", "notes", mode="before")
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
            raise ValueError("Material name is required.")
        return value

    @field_validator("category")
    @classmethod
    def category_not_blank(cls, value):
        if not value:
            raise ValueError("Category is required.")
        return value

    @field_validator("minimum_stock")
    @classmethod
    def round_minimum_stock(cls, value):
        return round_stock(value)

    @field_validator("purchase_price")
    @classmethod
    def round_purchase_price(cls, value):
        return round(value, 2)


class InventoryItemCreate(InventoryItemBase):
    """Request body for creating a raw material with its opening stock."""

    initial_quantity: float = Field(default=0.0, ge=0, le=999999)

    @field_validator("initial_quantity", mode="before")
    @classmethod
    def reject_boolean_quantity(cls, value):
        if isinstance(value, bool):
            raise ValueError("Value must be a number.")
        return value

    @field_validator("initial_quantity")
    @classmethod
    def round_initial_quantity(cls, value):
        return round_stock(value)


class InventoryItemUpdate(InventoryItemBase):
    """Request body for replacing a raw material (full update via PUT).

    Note: `current_quantity` is intentionally absent — stock levels change
    only through stock transactions so every movement stays in the history.
    """


class StockTransactionCreate(BaseModel):
    """Request body for recording a stock movement.

    - "Stock In" / "Stock Out": quantity is the amount moved, must be > 0.
    - "Adjustment": quantity is the NEW total after a physical count, >= 0.
    """

    transaction_type: Literal["Stock In", "Stock Out", "Adjustment"]
    quantity: float = Field(..., ge=0, le=999999)
    note: str | None = Field(default=None, max_length=200)

    @field_validator("quantity", mode="before")
    @classmethod
    def reject_boolean_quantity(cls, value):
        if isinstance(value, bool):
            raise ValueError("Value must be a number.")
        return value

    @field_validator("note", mode="before")
    @classmethod
    def strip_and_empty_to_none(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip()
        return value or None

    @field_validator("quantity")
    @classmethod
    def quantity_rules_by_type(cls, value, info):
        transaction_type = info.data.get("transaction_type")
        if transaction_type in ("Stock In", "Stock Out") and value <= 0:
            raise ValueError(f"Quantity must be greater than zero for {transaction_type}.")
        return round_stock(value)


class StockTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    transaction_type: str
    quantity: float
    balance_after: float
    note: str | None
    created_at: datetime


class StockTransactionWithItemRead(StockTransactionRead):
    """History row that also carries the material name (for global history)."""

    item_name: str = ""


class InventoryItemSummaryRead(BaseModel):
    """Inventory item row for tables/lists, including computed flags."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    unit: str
    current_quantity: float
    minimum_stock: float
    purchase_price: float
    supplier_id: int | None
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime | None
    supplier: SupplierBrief | None = None
    is_low_stock: bool = False
    transaction_count: int = 0


class InventoryItemDetailRead(InventoryItemSummaryRead):
    """Full item detail plus its recent stock movements."""

    transactions: list[StockTransactionRead] = []


class InventorySummary(BaseModel):
    """Counters for the inventory page header and later the dashboard."""

    total_items: int
    active_items: int
    low_stock_items: int
    total_suppliers: int
