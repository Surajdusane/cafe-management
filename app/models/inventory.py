from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

UNITS = ["Kg", "Gram", "Litre", "Millilitre", "Piece", "Packet", "Box"]
TRANSACTION_TYPES = ["Stock In", "Stock Out", "Adjustment"]


class InventoryItem(Base):
    """A raw material kept in stock (milk, coffee beans, sugar...).

    `current_quantity` is the live stock level. It is changed only through
    stock transactions (Stock In / Stock Out / Adjustment) so every movement
    leaves a history row behind.
    """

    __tablename__ = "inventory_items"
    __table_args__ = (UniqueConstraint("name", name="uq_inventory_items_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    unit: Mapped[str] = mapped_column(String(12), nullable=False)  # one of UNITS
    current_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    minimum_stock: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # Optional preferred supplier; deleting a supplier keeps the material
    # usable by clearing this link (ON DELETE SET NULL).
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    supplier: Mapped["Supplier | None"] = relationship(  # noqa: F821 - defined in supplier.py
        back_populates="inventory_items"
    )
    transactions: Mapped[list["InventoryTransaction"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="InventoryTransaction.id.desc()",
    )

    @property
    def is_low_stock(self) -> bool:
        """Low stock means at or below the minimum level (covers out-of-stock too)."""
        return self.current_quantity <= self.minimum_stock


class InventoryTransaction(Base):
    """One recorded stock movement for a raw material.

    - Stock In:      quantity units added to stock
    - Stock Out:     quantity units removed from stock (rejected if not enough)
    - Adjustment:    quantity is the NEW total after a physical count correction

    `balance_after` snapshots the stock level once the movement is applied,
    which keeps the history readable even as later movements change the level.
    """

    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(12), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)
    note: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    item: Mapped["InventoryItem"] = relationship(back_populates="transactions")
