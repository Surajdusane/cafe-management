from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.salary import SalaryCreate, SalaryRead, SalaryUpdate
from app.services import salary_service

router = APIRouter(prefix="/api/salaries", tags=["Salaries"])


def _serialize(salary) -> dict:
    return SalaryRead.model_validate(salary).model_dump(mode="json")


@router.get("")
def list_salaries(
    employee_id: int | None = Query(default=None, gt=0),
    month: str | None = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    payment_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Salary history, newest month first. Filter by employee, month or status."""
    salaries = salary_service.list_salaries(
        db, employee_id=employee_id, month=month, payment_status=payment_status
    )
    data = {"items": [_serialize(s) for s in salaries], "count": len(salaries)}
    return {"success": True, "data": data}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_salary(payload: SalaryCreate, db: Session = Depends(get_db)) -> dict:
    salary = salary_service.create_salary(db, payload)
    return {"success": True, "data": _serialize(salary), "message": "Salary record created."}


@router.get("/{salary_id}")
def read_salary(salary_id: int, db: Session = Depends(get_db)) -> dict:
    salary = salary_service.get_salary_or_404(db, salary_id)
    return {"success": True, "data": _serialize(salary)}


@router.put("/{salary_id}")
def update_salary(
    salary_id: int,
    payload: SalaryUpdate,
    db: Session = Depends(get_db),
) -> dict:
    salary = salary_service.update_salary(db, salary_id, payload)
    return {"success": True, "data": _serialize(salary), "message": "Salary record updated."}


@router.delete("/{salary_id}")
def delete_salary(salary_id: int, db: Session = Depends(get_db)) -> dict:
    salary_service.delete_salary(db, salary_id)
    return {"success": True, "data": None, "message": "Salary record deleted."}
