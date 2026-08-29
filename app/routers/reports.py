from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/sales")
def sales_report(
    period: str = Query(default="daily", pattern=r"^(daily|weekly|monthly)$"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Paid-order sales series, daily / weekly / monthly."""
    data = report_service.sales_report(db, period, start_date, end_date)
    return {"success": True, "data": data}


@router.get("/orders")
def orders_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Order breakdown by status and by date."""
    data = report_service.orders_report(db, start_date, end_date)
    return {"success": True, "data": data}


@router.get("/inventory")
def inventory_report(
    report_type: str = Query(default="current", pattern=r"^(current|low|movements)$"),
    db: Session = Depends(get_db),
) -> dict:
    """Current stock, low stock or recent stock movements."""
    data = report_service.inventory_report(db, report_type)
    return {"success": True, "data": data}


@router.get("/purchases")
def purchases_report(
    group_by: str = Query(default="date", pattern=r"^(supplier|date)$"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Purchase totals grouped by supplier or by date."""
    data = report_service.purchases_report(db, group_by, start_date, end_date)
    return {"success": True, "data": data}


@router.get("/salaries")
def salaries_report(db: Session = Depends(get_db)) -> dict:
    """Monthly salary expense across the whole history."""
    data = report_service.salaries_report(db)
    return {"success": True, "data": data}


@router.get("/expenses")
def expenses_report(
    group_by: str = Query(default="category", pattern=r"^(category|date)$"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Expense totals grouped by category or by date."""
    data = report_service.expenses_report(db, group_by, start_date, end_date)
    return {"success": True, "data": data}


@router.get("/profit")
def profit_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Estimated profit: Sales − Purchases − Salaries − Expenses."""
    data = report_service.profit_report(db, start_date, end_date)
    return {"success": True, "data": data}
