from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CafeSetting(Base):
    """Single-row table (id is always 1) holding the cafe profile used across the system."""

    __tablename__ = "cafe_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    cafe_name: Mapped[str] = mapped_column(String(100), nullable=False, default="My Cafe")
    address: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(15))
    email: Mapped[str | None] = mapped_column(String(100))
    logo_url: Mapped[str | None] = mapped_column(String(300))
    tax_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="₹")
    receipt_footer: Mapped[str | None] = mapped_column(String(200))
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
