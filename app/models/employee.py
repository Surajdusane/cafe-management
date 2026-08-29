from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Employee(Base):
    """A cafe staff member (manager, chef, waiter...).

    `base_salary` is the amount that applies to the chosen `salary_type`
    (a monthly amount, a daily rate or an hourly rate). It is only a
    reference value — actual payments are recorded separately as Salary
    rows, which copy the base salary used at payment time.
    """

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    mobile: Mapped[str] = mapped_column(String(15), nullable=False)
    email: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    salary_type: Mapped[str] = mapped_column(String(10), nullable=False)
    base_salary: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    salaries: Mapped[list["Salary"]] = relationship(  # noqa: F821 - defined in salary.py
        back_populates="employee", cascade="all, delete-orphan", order_by="Salary.id"
    )
