"""Report service (Phase 14).

Pure read-only aggregations over recorded data. Every number here is
recomputed live from the database — nothing is stored on the reports side.

Money definitions used throughout:
- "Sales"      : total of PAID orders (collected revenue).
- "Purchases"  : total of purchase records.
- "Salaries"   : net salary paid in the selected period.
- "Expenses"   : recorded expense amounts.

The profit summary is explicitly labelled an ESTIMATED management summary
because salaries are keyed by month (not by an exact date), so the figure is an
approximation, not a precise ledger balance.
"""

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.order import Order
from app.models.purchase import Purchase
from app.models.salary import Salary


def _round(value: float) -> float:
    return round(value or 0.0, 2)


def _iter_dates(start: date, end: date):
    """Yield each calendar date from start to end inclusive."""
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _month_label(yyyy_mm: str) -> str:
    """Turn '2026-08' into a short readable label like 'Aug 26'."""
    year, month = yyyy_mm.split("-")
    return f"{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][int(month) - 1]} {year[2:]}"


def _months_between(start: date | None, end: date | None) -> set[str]:
    """Set of 'YYYY-MM' strings covered by a date range (inclusive)."""
    if start is None and end is None:
        return set()
    s = start or date(2000, 1, 1)
    e = end or date(2100, 12, 31)
    result = set()
    cursor = date(s.year, s.month, 1)
    while cursor <= e:
        result.add(cursor.strftime("%Y-%m"))
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    return result


# --------------------------------------------------------------------------- #
# Sales — daily / weekly / monthly
# --------------------------------------------------------------------------- #

def sales_report(db: Session, period: str, start_date: date | None, end_date: date | None) -> dict:
    """Series of paid-order sales bucketed into a date/Month label.

    - daily:   one point per calendar day in the selected (or last-14-day) range
    - weekly:  the last 7 calendar days, one point per day (daily view)
    - monthly: one point per 'YYYY-MM' month in the range
    """
    query = db.scalars(
        select(Order)
        .where(Order.payment_status == "Paid")
    ).all()

    if period == "monthly":
        # Monthly also honours the date filter, bucketing into 'YYYY-MM'.
        s = start_date or date(2000, 1, 1)
        e = end_date or date(2100, 12, 31)
        buckets: dict[str, dict] = {}
        for order in query:
            order_date = order.created_at.date()
            if s <= order_date <= e:
                key = order.created_at.strftime("%Y-%m")
                b = buckets.setdefault(key, {"amount": 0.0, "orders": 0})
                b["amount"] += order.total
                b["orders"] += 1
        keys = sorted(buckets.keys())
        labels = [_month_label(k) for k in keys]
        amounts = [_round(buckets[k]["amount"]) for k in keys]
        order_counts = [buckets[k]["orders"] for k in keys]
        period_label = "Monthly"
    else:
        # daily and weekly both render as a per-day series.
        if period == "weekly":
            default_days = 6  # a rolling last-7-day window
        else:
            default_days = 13  # daily shows the last 14 days
        if start_date is None:
            start_date = date.today() - timedelta(days=default_days)
        if end_date is None:
            end_date = date.today()
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        per_day: dict[date, dict] = {}
        for order in query:
            order_date = order.created_at.date()
            if start_date <= order_date <= end_date:
                b = per_day.setdefault(order_date, {"amount": 0.0, "orders": 0})
                b["amount"] += order.total
                b["orders"] += 1

        labels, amounts, order_counts = [], [], []
        for day in _iter_dates(start_date, end_date):
            b = per_day.get(day, {"amount": 0.0, "orders": 0})
            labels.append(day.strftime("%d %b"))
            amounts.append(_round(b["amount"]))
            order_counts.append(b["orders"])

        period_label = "Weekly" if period == "weekly" else "Daily"

    total = _round(sum(amounts))
    total_orders = sum(order_counts)
    return {
        "period": period,
        "period_label": period_label,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "summary": {
            "sales_total": total,
            "orders": total_orders,
            "avg_order": _round(total / total_orders) if total_orders else 0.0,
        },
        "series": {
            "labels": labels,
            "amounts": amounts,
            "orders": order_counts,
        },
    }


# --------------------------------------------------------------------------- #
# Orders — by date and by status
# --------------------------------------------------------------------------- #

def orders_report(db: Session, start_date: date | None, end_date: date | None) -> dict:
    query = db.scalars(select(Order)).all()

    filtered = [
        o for o in query
        if (start_date is None or o.created_at.date() >= start_date)
        and (end_date is None or o.created_at.date() <= end_date)
    ]

    if start_date is None:
        start_date = date.today() - timedelta(days=13)
    if end_date is None:
        end_date = date.today()

    by_status: list[dict] = []
    by_date: list[dict] = []
    per_status: dict[str, dict] = {}
    per_day: dict[date, dict] = {}

    for order in filtered:
        ps = per_status.setdefault(order.status, {"status": order.status, "count": 0, "total": 0.0})
        ps["count"] += 1
        ps["total"] += order.total
        pd = per_day.setdefault(order.created_at.date(), {"date": "", "count": 0, "total": 0.0})
        pd["count"] += 1
        pd["total"] += order.total

    for day in _iter_dates(start_date, end_date):
        b = per_day.get(day, {"count": 0, "total": 0.0})
        by_date.append({"date": day.isoformat(), "label": day.strftime("%d %b"), **b})

    order_priority = {"Pending": 0, "Preparing": 1, "Ready": 2, "Completed": 3, "Cancelled": 4}
    for item in sorted(per_status.values(), key=lambda i: order_priority.get(i["status"], 9)):
        item["total"] = _round(item["total"])
        by_status.append(item)

    total = _round(sum(i["total"] for i in by_status))
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "summary": {"count": len(filtered), "total": total},
        "by_status": by_status,
        "by_date": by_date,
    }


# --------------------------------------------------------------------------- #
# Inventory — current stock / low stock / movements
# --------------------------------------------------------------------------- #

def inventory_report(db: Session, report_type: str) -> dict:
    items = db.scalars(select(InventoryItem).order_by(InventoryItem.name)).all()
    rows = [
        {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "unit": item.unit,
            "current_quantity": item.current_quantity,
            "minimum_stock": item.minimum_stock,
            "purchase_price": item.purchase_price,
            "is_low_stock": item.current_quantity <= item.minimum_stock,
            "is_active": item.is_active,
        }
        for item in items
    ]

    if report_type == "low":
        rows = [r for r in rows if r["is_low_stock"]]
    elif report_type == "current":
        rows = [r for r in rows if r["is_active"]]

    if report_type == "movements":
        movements = db.scalars(
            select(InventoryTransaction).order_by(InventoryTransaction.id.desc()).limit(300)
        ).all()
        rows = [
            {
                "item_name": m.item.name,
                "transaction_type": m.transaction_type,
                "quantity": m.quantity,
                "balance_after": m.balance_after,
                "note": m.note,
                "created_at": m.created_at.isoformat(),
            }
            for m in movements
        ]

    low_total = sum(1 for item in items if item.current_quantity <= item.minimum_stock)
    summary = {
        "active_items": sum(1 for item in items if item.is_active),
        "low_stock": low_total,
        "total_value": _round(
            sum(item.current_quantity * item.purchase_price for item in items if item.is_active)
        ),
    }
    return {"report_type": report_type, "summary": summary, "items": rows}


# --------------------------------------------------------------------------- #
# Purchases — by supplier and by date
# --------------------------------------------------------------------------- #

def purchases_report(db: Session, group_by: str, start_date: date | None, end_date: date | None) -> dict:
    purchases = db.scalars(select(Purchase)).all()
    filtered = [
        p for p in purchases
        if (start_date is None or p.purchase_date >= start_date)
        and (end_date is None or p.purchase_date <= end_date)
    ]

    if group_by == "supplier":
        per: dict[str, dict] = {}
        for p in filtered:
            b = per.setdefault(p.supplier_name, {"name": p.supplier_name, "count": 0, "total": 0.0})
            b["count"] += 1
            b["total"] += p.total
        rows = [{"name": k, **v} for k, v in sorted(per.items(), key=lambda kv: kv[1]["total"], reverse=True)]
    else:  # by date
        per_by_date: dict[date, dict] = {}
        for p in filtered:
            b = per_by_date.setdefault(p.purchase_date, {"total": 0.0, "count": 0})
            b["total"] += p.total
            b["count"] += 1
        rows = [
            {"date": d.isoformat(), "label": d.strftime("%d %b %y"), "total": _round(v["total"]), "count": v["count"]}
            for d, v in sorted(per_by_date.items(), key=lambda kv: kv[0])
        ]

    total = _round(sum(p.total for p in filtered))
    return {
        "group_by": group_by,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "summary": {"count": len(filtered), "total": total},
        "items": rows,
    }


# --------------------------------------------------------------------------- #
# Salaries — monthly expense
# --------------------------------------------------------------------------- #

def salaries_report(db: Session) -> dict:
    salaries = db.scalars(select(Salary)).all()
    per_month: dict[str, dict] = {}
    for s in salaries:
        b = per_month.setdefault(s.salary_month, {"month": s.salary_month, "count": 0, "total": 0.0})
        b["count"] += 1
        b["total"] += s.net_salary
    rows = [
        {"month": m, "count": v["count"], "total": _round(v["total"])}
        for m, v in sorted(per_month.items(), reverse=True)
    ]
    return {
        "summary": {"total": _round(sum(s.net_salary for s in salaries)), "records": len(salaries)},
        "items": rows,
    }


# --------------------------------------------------------------------------- #
# Expenses — by category and by date
# --------------------------------------------------------------------------- #

def expenses_report(db: Session, group_by: str, start_date: date | None, end_date: date | None) -> dict:
    expenses = db.scalars(select(Expense)).all()
    filtered = [
        e for e in expenses
        if (start_date is None or e.expense_date >= start_date)
        and (end_date is None or e.expense_date <= end_date)
    ]

    if group_by == "category":
        per: dict[str, dict] = {}
        for e in filtered:
            b = per.setdefault(e.category, {"category": e.category, "count": 0, "total": 0.0})
            b["count"] += 1
            b["total"] += e.amount
        rows = [{"category": k, **v} for k, v in sorted(per.items(), key=lambda kv: kv[1]["total"], reverse=True)]
    else:  # by date
        per_by_date: dict[date, dict] = {}
        for e in filtered:
            b = per_by_date.setdefault(e.expense_date, {"total": 0.0, "count": 0})
            b["total"] += e.amount
            b["count"] += 1
        rows = [
            {"date": d.isoformat(), "label": d.strftime("%d %b %y"), "total": _round(v["total"]), "count": v["count"]}
            for d, v in sorted(per_by_date.items(), key=lambda kv: kv[0])
        ]

    total = _round(sum(e.amount for e in filtered))
    return {
        "group_by": group_by,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "summary": {"count": len(filtered), "total": total},
        "items": rows,
    }


# --------------------------------------------------------------------------- #
# Estimated profit summary
# --------------------------------------------------------------------------- #

def profit_report(db: Session, start_date: date | None, end_date: date | None) -> dict:
    """Estimated profit = Sales − Purchases − Salaries − Expenses.

    Labelled ESTIMATED because salaries are matched by month within the range,
    not by an exact day. Purchases/expenses match on their recorded date.
    """
    sales = sum(
        o.total for o in
        db.scalars(select(Order).where(Order.payment_status == "Paid")).all()
        if (start_date is None or o.created_at.date() >= start_date)
        and (end_date is None or o.created_at.date() <= end_date)
    )
    purchases = sum(
        p.total for p in
        db.scalars(select(Purchase)).all()
        if (start_date is None or p.purchase_date >= start_date)
        and (end_date is None or p.purchase_date <= end_date)
    )
    expenses = sum(
        e.amount for e in
        db.scalars(select(Expense)).all()
        if (start_date is None or e.expense_date >= start_date)
        and (end_date is None or e.expense_date <= end_date)
    )

    months = _months_between(start_date, end_date)
    salaries_stmt = select(Salary)
    if months:
        salaries_stmt = salaries_stmt.where(Salary.salary_month.in_(months))
    salaries = sum(s.net_salary for s in db.scalars(salaries_stmt).all())

    sales_r = _round(sales)
    purchases_r = _round(purchases)
    salaries_r = _round(salaries)
    expenses_r = _round(expenses)
    profit = _round(sales_r - purchases_r - salaries_r - expenses_r)

    return {
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "components": {
            "sales": sales_r,
            "purchases": purchases_r,
            "salaries": salaries_r,
            "expenses": expenses_r,
        },
        "estimated_profit": profit,
        "labelled_note": "Estimated management summary — salaries are matched by month, not by an exact day.",
    }
