from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.employee import Employee
from app.models.salary import Salary


def get_employee_or_404(db: Session, employee_id: int) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} was not found. Create them first.",
        )
    return employee


def _raise_duplicate_month(db: Session, employee_id: int, month: str, exclude_id: int | None = None) -> None:
    """One salary record per employee per month."""
    stmt = select(Salary).where(Salary.employee_id == employee_id, Salary.salary_month == month)
    if exclude_id is not None:
        stmt = stmt.where(Salary.id != exclude_id)
    existing = db.scalar(stmt)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A salary record for {month} already exists for this employee.",
        )


def list_salaries(
    db: Session,
    employee_id: int | None = None,
    month: str | None = None,
    payment_status: str | None = None,
) -> list[Salary]:
    """Salary history ordered newest month first."""
    conditions = []
    if employee_id is not None:
        conditions.append(Salary.employee_id == employee_id)
    if month:
        conditions.append(Salary.salary_month == month)
    if payment_status:
        conditions.append(Salary.payment_status == payment_status)

    stmt = (
        select(Salary)
        .options(selectinload(Salary.employee))
        .where(*conditions)
        .order_by(Salary.salary_month.desc(), Salary.id.desc())
    )
    return list(db.scalars(stmt))


def get_salary_or_404(db: Session, salary_id: int) -> Salary:
    stmt = (
        select(Salary)
        .options(selectinload(Salary.employee))
        .where(Salary.id == salary_id)
    )
    salary = db.scalar(stmt)
    if salary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Salary record with id {salary_id} was not found.",
        )
    return salary


def calculate_net_salary(base_salary: float, bonus: float, deduction: float) -> float:
    """The one formula the whole module is built on: net = base + bonus - deduction."""
    return round(base_salary + bonus - deduction, 2)


def _resolve_base_salary(db: Session, payload) -> float:
    """A missing base_salary falls back to the employee's current base salary."""
    if payload.base_salary is not None:
        return round(payload.base_salary, 2)
    employee = get_employee_or_404(db, payload.employee_id)
    return round(employee.base_salary, 2)


def create_salary(db: Session, payload) -> Salary:
    employee = get_employee_or_404(db, payload.employee_id)
    _raise_duplicate_month(db, payload.employee_id, payload.salary_month)

    base_salary = _resolve_base_salary(db, payload)
    salary = Salary(
        employee_id=employee.id,
        salary_month=payload.salary_month,
        base_salary=base_salary,
        bonus=payload.bonus,
        deduction=payload.deduction,
        net_salary=calculate_net_salary(base_salary, payload.bonus, payload.deduction),
        payment_status=payload.payment_status,
        # Marking a salary Paid without a date defaults to today.
        payment_date=payload.payment_date or (date.today() if payload.payment_status == "Paid" else None),
        notes=payload.notes,
    )
    db.add(salary)
    db.commit()
    db.refresh(salary)
    return salary


def update_salary(db: Session, salary_id: int, payload) -> Salary:
    salary = get_salary_or_404(db, salary_id)
    get_employee_or_404(db, payload.employee_id)
    _raise_duplicate_month(db, payload.employee_id, payload.salary_month, exclude_id=salary_id)

    base_salary = _resolve_base_salary(db, payload)
    salary.employee_id = payload.employee_id
    salary.salary_month = payload.salary_month
    salary.base_salary = base_salary
    salary.bonus = payload.bonus
    salary.deduction = payload.deduction
    salary.net_salary = calculate_net_salary(base_salary, payload.bonus, payload.deduction)
    salary.payment_status = payload.payment_status
    salary.payment_date = payload.payment_date or (
        date.today() if payload.payment_status == "Paid" else None
    )
    salary.notes = payload.notes
    db.commit()
    db.refresh(salary)
    return salary


def delete_salary(db: Session, salary_id: int) -> None:
    salary = get_salary_or_404(db, salary_id)
    db.delete(salary)
    db.commit()
