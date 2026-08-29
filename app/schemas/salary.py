import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.employee import EmployeeBrief

MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
PAYMENT_STATUSES = ("Paid", "Unpaid")


def round_amount(value: float) -> float:
    return round(value, 2)


class SalaryBase(BaseModel):
    """Shared fields and rules for creating/updating a salary record.

    `base_salary` may be left out — the service then copies the employee's
    current base salary (see salary_service.create_salary/update_salary).
    """

    employee_id: int = Field(gt=0)
    salary_month: str
    base_salary: float | None = Field(default=None, ge=0, le=99999999)
    bonus: float = Field(default=0, ge=0, le=99999999)
    deduction: float = Field(default=0, ge=0, le=99999999)
    payment_status: str = "Unpaid"
    payment_date: date | None = None
    notes: str | None = Field(default=None, max_length=255)

    @field_validator("employee_id", "base_salary", "bonus", "deduction", mode="before")
    @classmethod
    def reject_boolean_numbers(cls, value):
        # bool is a subclass of int; True/False must not pass as 0/1 amounts.
        if isinstance(value, bool):
            raise ValueError("Value must be a number.")
        return value

    @field_validator("salary_month")
    @classmethod
    def month_format_is_yyyy_mm(cls, value):
        value = (value or "").strip()
        if not MONTH_PATTERN.fullmatch(value):
            raise ValueError("Salary month must use the YYYY-MM format, e.g. 2026-08.")
        year, month = value.split("-")
        if not 2000 <= int(year) <= 2100:
            raise ValueError("Salary month year must be between 2000 and 2100.")
        return value

    @field_validator("payment_status")
    @classmethod
    def status_in_allowed_list(cls, value):
        if value not in PAYMENT_STATUSES:
            raise ValueError("Payment status must be Paid or Unpaid.")
        return value

    @field_validator("bonus", "deduction")
    @classmethod
    def amount_not_negative(cls, value):
        if value < 0:
            raise ValueError("Bonus and deduction cannot be negative.")
        return round_amount(value)

    @model_validator(mode="after")
    def net_salary_cannot_be_negative(self):
        base = self.base_salary if self.base_salary is not None else 0
        if self.deduction > base + self.bonus:
            raise ValueError(
                "Deduction is larger than base salary plus bonus — net salary would be negative."
            )
        return self

    @field_validator("notes", mode="before")
    @classmethod
    def strip_notes(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class SalaryCreate(SalaryBase):
    """Request body for creating a salary record."""


class SalaryUpdate(SalaryBase):
    """Request body for replacing a salary record (full update via PUT)."""


class SalaryRead(BaseModel):
    """Salary returned by the API; includes a summary of the employee."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    employee: EmployeeBrief
    salary_month: str
    base_salary: float
    bonus: float
    deduction: float
    net_salary: float
    payment_status: str
    payment_date: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime | None
