import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
PHONE_PATTERN = re.compile(r"^[6-9]\d{9}$")

EMPLOYEE_ROLES = ("Manager", "Cashier", "Chef", "Waiter", "Helper", "Cleaner")
SALARY_TYPES = ("Monthly", "Daily", "Hourly")


class EmployeeBase(BaseModel):
    """Shared fields and rules for creating/updating an employee."""

    name: str = Field(min_length=1, max_length=100)
    mobile: str = Field(min_length=10, max_length=10)
    email: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    role: str
    joining_date: date
    salary_type: str
    base_salary: float = Field(ge=0, le=99999999)
    is_active: bool = True

    @field_validator(
        "name",
        "mobile",
        "email",
        "address",
        mode="before",
    )
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
            raise ValueError("Employee name is required.")
        return value

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, value):
        if not PHONE_PATTERN.fullmatch(value or ""):
            raise ValueError("Enter a valid 10-digit mobile number.")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if value is not None and not EMAIL_PATTERN.fullmatch(value.lower()):
            raise ValueError("Enter a valid email address.")
        return value.lower() if value else value

    @field_validator("role")
    @classmethod
    def role_in_allowed_list(cls, value):
        if value not in EMPLOYEE_ROLES:
            allowed = ", ".join(EMPLOYEE_ROLES)
            raise ValueError(f"Role must be one of: {allowed}.")
        return value

    @field_validator("salary_type")
    @classmethod
    def salary_type_in_allowed_list(cls, value):
        if value not in SALARY_TYPES:
            allowed = ", ".join(SALARY_TYPES)
            raise ValueError(f"Salary type must be one of: {allowed}.")
        return value

    @field_validator("base_salary", mode="before")
    @classmethod
    def reject_boolean_numbers(cls, value):
        # bool is a subclass of int; True/False must not pass as 0/1 amounts.
        if isinstance(value, bool):
            raise ValueError("Value must be a number.")
        return value

    @field_validator("base_salary")
    @classmethod
    def base_salary_not_negative(cls, value):
        if value < 0:
            raise ValueError("Base salary cannot be negative.")
        return round(value, 2)

    @field_validator("joining_date")
    @classmethod
    def joining_date_not_in_future(cls, value):
        if value > date.today():
            raise ValueError("Joining date cannot be in the future.")
        return value


class EmployeeCreate(EmployeeBase):
    """Request body for creating an employee."""


class EmployeeUpdate(EmployeeBase):
    """Request body for replacing an employee (full update via PUT)."""


class EmployeeBrief(BaseModel):
    """Lightweight employee info embedded in dropdowns and salary responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role: str
    salary_type: str
    base_salary: float
    is_active: bool


class EmployeeRead(BaseModel):
    """Employee returned by the API. salary_count is filled by the service."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    mobile: str
    email: str | None
    address: str | None
    role: str
    joining_date: date
    salary_type: str
    base_salary: float
    is_active: bool
    salary_count: int = 0
    created_at: datetime
    updated_at: datetime | None
