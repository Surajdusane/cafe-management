from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.expense import EXPENSE_CATEGORIES, PAYMENT_METHODS
from app.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate
from app.services import expense_service

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


def _serialize(expense) -> dict:
    return ExpenseRead.model_validate(expense).model_dump(mode="json")


@router.get("/options")
def expense_options() -> dict:
    """Fixed choice lists (categories, payment methods) so the UI never hard-codes them."""
    return {
        "success": True,
        "data": {"categories": EXPENSE_CATEGORIES, "payment_methods": PAYMENT_METHODS},
    }


@router.get("")
def list_expenses(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None),
    payment_method: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Expense history newest first with search, category, payment and date
    filters. `summary` carries totals for the page's stat cards."""
    expenses = expense_service.list_expenses(
        db,
        search=search,
        category=category,
        payment_method=payment_method,
        start_date=start_date,
        end_date=end_date,
    )
    data = {
        "items": [_serialize(e) for e in expenses],
        "count": len(expenses),
        "summary": expense_service.summarize(expenses),
    }
    return {"success": True, "data": data}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)) -> dict:
    expense = expense_service.create_expense(db, payload)
    return {"success": True, "data": _serialize(expense), "message": "Expense recorded."}


@router.get("/{expense_id}")
def read_expense(expense_id: int, db: Session = Depends(get_db)) -> dict:
    expense = expense_service.get_expense_or_404(db, expense_id)
    return {"success": True, "data": _serialize(expense)}


@router.put("/{expense_id}")
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    db: Session = Depends(get_db),
) -> dict:
    expense = expense_service.update_expense(db, expense_id, payload)
    return {"success": True, "data": _serialize(expense), "message": "Expense updated."}


@router.delete("/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)) -> dict:
    expense_service.delete_expense(db, expense_id)
    return {"success": True, "data": None, "message": "Expense deleted."}
