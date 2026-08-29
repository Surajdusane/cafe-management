from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.employee import EMPLOYEE_ROLES, EmployeeCreate, EmployeeRead, EmployeeUpdate
from app.services import employee_service

router = APIRouter(prefix="/api/employees", tags=["Employees"])


def _serialize(employee) -> dict:
    return EmployeeRead.model_validate(employee).model_dump(mode="json")


@router.get("")
def list_employees(
    search: str | None = Query(default=None, max_length=100),
    role: str | None = Query(default=None),
    include_inactive: bool = True,
    db: Session = Depends(get_db),
) -> dict:
    """List employees (ordered by name), each with a live salary-record count."""
    if role is not None and role not in EMPLOYEE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unknown role filter.",
        )
    employees = employee_service.list_employees(db, search=search, role=role, include_inactive=include_inactive)
    data = {"items": [_serialize(e) for e in employees], "count": len(employees)}
    return {"success": True, "data": data}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)) -> dict:
    employee = employee_service.create_employee(db, payload)
    return {"success": True, "data": _serialize(employee), "message": "Employee created."}


@router.get("/{employee_id}")
def read_employee(employee_id: int, db: Session = Depends(get_db)) -> dict:
    employee = employee_service.get_employee_or_404(db, employee_id)
    return {"success": True, "data": _serialize(employee)}


@router.put("/{employee_id}")
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
) -> dict:
    employee = employee_service.update_employee(db, employee_id, payload)
    return {"success": True, "data": _serialize(employee), "message": "Employee updated."}


@router.delete("/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)) -> dict:
    employee_service.delete_employee(db, employee_id)
    return {"success": True, "data": None, "message": "Employee deleted."}
