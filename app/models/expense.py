from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

EXPENSE_CATEGORIES = [
    "Electricity",
    "Gas",
    "Rent",
    "Maintenance",
    "Cleaning",
    "Internet",
    "Miscellaneous",
]

# Kept in sync with the billing payment methods so reports can slice consistently.
PAYMENT_METHODS = ["Cash", "UPI", "Card", "Other"]


class Expense(Base):
    """One recorded cafe running cost (electricity, rent, maintenance...).

    Amount and date are frozen at entry time so re-typing or later edits to a
    shared category name never rewrite the history. Deletion is allowed without
    breakage because an expense row carries no foreign keys — it simply records
    a dated money outflow.
    """

    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(10), nullable=False, default="Cash")
    notes: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
