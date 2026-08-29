from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.expense import Expense


def _round(value: float) -> float:
    return round(value, 2)


def list_expenses(
    db: Session,
    search: str | None = None,
    category: str | None = None,
    payment_method: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Expense]:
    """Expense history newest first with search, category, payment and date filters."""
    stmt = select(Expense)
    conditions = []
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(Expense.title.ilike(term), Expense.notes.ilike(term)))
    if category:
        conditions.append(Expense.category == category)
    if payment_method:
        conditions.append(Expense.payment_method == payment_method)
    if start_date is not None:
        conditions.append(Expense.expense_date >= start_date)
    if end_date is not None:
        conditions.append(Expense.expense_date <= end_date)
    if conditions:
        stmt = stmt.where(*conditions)
    # Newest expenses first — staff care about the latest outflows.
    stmt = stmt.order_by(Expense.expense_date.desc(), Expense.id.desc())
    return list(db.scalars(stmt))


def summarize(expenses: list[Expense]) -> dict:
    """Stat-card totals over the filtered result set."""
    total = _round(sum(e.amount for e in expenses))
    by_category: dict[str, float] = {}
    for e in expenses:
        by_category[e.category] = _round(by_category.get(e.category, 0.0) + e.amount)
    return {
        "count": len(expenses),
        "total_amount": total,
        "categories": len(by_category),
    }


def get_expense_or_404(db: Session, expense_id: int) -> Expense:
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} was not found.",
        )
    return expense


def create_expense(db: Session, payload) -> Expense:
    expense = Expense(
        title=payload.title,
        category=payload.category,
        amount=payload.amount,
        expense_date=payload.expense_date or date.today(),
        payment_method=payload.payment_method,
        notes=payload.notes,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def update_expense(db: Session, expense_id: int, payload) -> Expense:
    expense = get_expense_or_404(db, expense_id)
    expense.title = payload.title
    expense.category = payload.category
    expense.amount = payload.amount
    expense.expense_date = payload.expense_date or date.today()
    expense.payment_method = payload.payment_method
    expense.notes = payload.notes
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense_id: int) -> None:
    expense = get_expense_or_404(db, expense_id)
    db.delete(expense)
    db.commit()
