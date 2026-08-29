from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Salary(Base):
    """One salary payment record for one employee for one month.

    Net salary is calculated once by the server when the record is saved
    (base + bonus - deduction) and never recomputed later, so editing an
    employee's base salary cannot silently rewrite past payments.
    An employee can have only one salary record per month — enforced by a
    unique constraint and a friendly 409 from the service layer.
    """

    __tablename__ = "salaries"
    __table_args__ = (
        UniqueConstraint("employee_id", "salary_month", name="uq_salaries_employee_month"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    # "YYYY-MM" text sorts correctly everywhere and matches <input type="month">.
    salary_month: Mapped[str] = mapped_column(String(7), nullable=False)
    base_salary: Mapped[float] = mapped_column(Float, nullable=False)
    bonus: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    deduction: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    net_salary: Mapped[float] = mapped_column(Float, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(10), nullable=False, default="Unpaid")
    payment_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    employee: Mapped["Employee"] = relationship(back_populates="salaries")  # noqa: F821
