from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Supplier(Base):
    """A supplier the cafe buys raw materials from (milk vendor, bean roaster...)."""

    __tablename__ = "suppliers"
    __table_args__ = (UniqueConstraint("name", name="uq_suppliers_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(15))
    email: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(255))
    materials_supplied: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    inventory_items: Mapped[list["InventoryItem"]] = relationship(  # noqa: F821 - defined in inventory.py
        back_populates="supplier"
    )
