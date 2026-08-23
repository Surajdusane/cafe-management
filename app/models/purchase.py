from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Purchase(Base):
    """One recorded purchase from a supplier.

    Like orders, money values are calculated once by the server when the
    purchase is recorded and never recomputed, so later price changes cannot
    rewrite history. Recording a purchase also increases inventory — both
    happen inside one database transaction (see purchase_service).
    """

    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    # SET NULL + name snapshot keeps old purchases readable after a supplier
    # is deleted (same idea as OrderItem's menu_item_id).
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True
    )
    supplier_name: Mapped[str] = mapped_column(String(100), nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payment_status: Mapped[str] = mapped_column(String(10), nullable=False, default="Unpaid")
    notes: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["PurchaseItem"]] = relationship(
        back_populates="purchase", cascade="all, delete-orphan", order_by="PurchaseItem.id"
    )


class PurchaseItem(Base):
    """One purchased material line. Name and unit are copied from the raw
    material at purchase time so history stays readable even if the material
    is renamed or deleted later."""

    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False
    )
    # SET NULL keeps the line (with its snapshots) after the material is deleted.
    inventory_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("inventory_items.id", ondelete="SET NULL"), nullable=True
    )
    item_name: Mapped[str] = mapped_column(String(120), nullable=False)
    unit: Mapped[str] = mapped_column(String(12), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    line_total: Mapped[float] = mapped_column(Float, nullable=False)

    purchase: Mapped["Purchase"] = relationship(back_populates="items")
