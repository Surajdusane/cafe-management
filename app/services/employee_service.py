from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.salary import Salary


def _salary_count_stmt():
    return (
        select(func.count(Salary.id))
        .where(Salary.employee_id == Employee.id)
        .correlate(Employee)
        .scalar_subquery()
    )


def list_employees(
    db: Session,
    search: str | None = None,
    role: str | None = None,
    include_inactive: bool = True,
) -> list[Employee]:
    """Return employees ordered by name, each with a live salary-record count."""
    conditions = []
    if search:
        term = f"%{search.strip()}%"
        conditions.append(
            or_(
                Employee.name.ilike(term),
                Employee.mobile.ilike(term),
                Employee.email.ilike(term),
                Employee.role.ilike(term),
            )
        )
    if role:
        conditions.append(Employee.role == role)
    if not include_inactive:
        conditions.append(Employee.is_active.is_(True))

    stmt = select(Employee, _salary_count_stmt().label("salary_count"))
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.order_by(Employee.name)

    employees: list[Employee] = []
    for employee, count in db.execute(stmt).all():
        employee.salary_count = count
        employees.append(employee)
    return employees


def get_employee_or_404(db: Session, employee_id: int) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} was not found.",
        )
    employee.salary_count = len(employee.salaries)
    return employee


def create_employee(db: Session, payload) -> Employee:
    employee = Employee(**payload.model_dump())
    employee.salary_count = 0
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def update_employee(db: Session, employee_id: int, payload) -> Employee:
    employee = get_employee_or_404(db, employee_id)

    for field, value in payload.model_dump().items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)

    employee.salary_count = len(employee.salaries)
    return employee


def delete_employee(db: Session, employee_id: int) -> None:
    """Delete an employee. Blocked while salary records exist so payment
    history (used by reports) can never disappear silently."""
    employee = get_employee_or_404(db, employee_id)
    if employee.salaries:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"{employee.name} has {len(employee.salaries)} salary record(s). "
                "Delete their salary history first."
            ),
        )
    db.delete(employee)
    db.commit()
