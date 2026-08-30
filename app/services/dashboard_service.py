"""Dashboard service (Phase 15).

Read-only aggregations that power the `GET /api/dashboard` endpoint. Just like
the Reports module, everything is recomputed live from recorded data — the
dashboard stores nothing of its own.

Definitions mirror the rest of the system:
- "Today's sales"   : total of PAID orders placed today (collected revenue).
- "Pending orders"  : orders still in Pending / Preparing / Ready.
- "Unpaid bills"    : total value of unpaid, non-cancelled orders (outstanding).
- "Low stock"       : active materials at or below their minimum level.
- "Monthly expenses": running costs recorded from the 1st of the present month.
- "Top sellers"     : ordered item names ranked by total quantity, ignoring
                      cancelled orders (a cancelled order never sold anything).
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.expense import Expense
from app.models.inventory import InventoryItem
from app.models.menu_item import MenuItem
from app.models.order import Order, OrderItem
from app.services.settings_service import get_or_create_settings

OPEN_ORDER_STATUSES = ("Pending", "Preparing", "Ready")
RECENT_ORDERS_LIMIT = 8


def _round(value: float) -> float:
    return round(value or 0.0, 2)


def _local_date(value: datetime) -> date:
    """Convert a naive-UTC stored timestamp to the cafe's local calendar date.

    `created_at` is saved as UTC (SQLite CURRENT_TIMESTAMP), but "today" must
    mean the local day — otherwise orders taken before 05:30 local time (UTC+5:30
    India, where local date is already one day ahead) would vanish from today's
    sales. Naive rows are interpreted as UTC and shifted to the local zone."""
    return value.replace(tzinfo=timezone.utc).astimezone().date()


def _serialize_order(order: Order) -> dict:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "order_type": order.order_type,
        "table_number": order.table_number,
        "status": order.status,
        "total": _round(order.total),
        "payment_status": order.payment_status,
        "payment_method": order.payment_method,
        "created_at": order.created_at.isoformat(),
    }


def dashboard_summary(db: Session) -> dict:
    today = date.today()
    month_start = today.replace(day=1)

    settings = get_or_create_settings(db)

    orders = db.scalars(select(Order)).all()

    today_orders = sum(1 for order in orders if _local_date(order.created_at) == today)
    today_sales = sum(
        order.total
        for order in orders
        if _local_date(order.created_at) == today and order.payment_status == "Paid"
    )
    pending_orders = sum(1 for order in orders if order.status in OPEN_ORDER_STATUSES)
    unpaid_bills = sum(
        order.total
        for order in orders
        if order.payment_status == "Unpaid" and order.status != "Cancelled"
    )

    menu_items = db.scalar(
        select(func.count(MenuItem.id)).where(MenuItem.is_available.is_(True))
    ) or 0

    inventory_items = db.scalars(select(InventoryItem)).all()
    low_stock = sum(
        1
        for item in inventory_items
        if item.is_active and item.current_quantity <= item.minimum_stock
    )

    employees = db.scalar(
        select(func.count(Employee.id)).where(Employee.is_active.is_(True))
    ) or 0

    monthly_expenses = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.expense_date >= month_start
        )
    ) or 0.0

    # Sales trend: a rolling last-7-days window (local calendar days).
    trend_start = today - timedelta(days=6)
    per_day: dict[date, dict] = {}
    for order in orders:
        order_date = _local_date(order.created_at)
        if order_date < trend_start or order_date > today:
            continue
        bucket = per_day.setdefault(order_date, {"amount": 0.0, "orders": 0})
        bucket["amount"] += order.total if order.payment_status == "Paid" else 0.0
        bucket["orders"] += 1
    trend_labels, trend_amounts, trend_orders = [], [], []
    for day in (trend_start + timedelta(days) for days in range(7)):
        bucket = per_day.get(day, {"amount": 0.0, "orders": 0})
        trend_labels.append(day.strftime("%a %d"))
        trend_amounts.append(_round(bucket["amount"]))
        trend_orders.append(bucket["orders"])

    top_rows = db.execute(
        select(OrderItem.item_name, func.sum(OrderItem.quantity))
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.status != "Cancelled")
        .group_by(OrderItem.item_name)
        .order_by(func.sum(OrderItem.quantity).desc(), OrderItem.item_name)
        .limit(5)
    ).all()
    top_items = [
        {"name": item_name, "quantity": int(quantity)}
        for item_name, quantity in top_rows
    ]

    recent = db.scalars(
        select(Order)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .limit(RECENT_ORDERS_LIMIT)
    ).all()

    return {
        "cafe": {
            "name": settings.cafe_name or "Cafe Desk",
            "currency": settings.currency or "₹",
        },
        "date": today.isoformat(),
        "stats": {
            "today_sales": _round(today_sales),
            "today_orders": today_orders,
            "pending_orders": pending_orders,
            "unpaid_bills": _round(unpaid_bills),
            "menu_items": menu_items,
            "low_stock": low_stock,
            "employees": employees,
            "monthly_expenses": _round(monthly_expenses),
        },
        "sales_trend": {
            "labels": trend_labels,
            "amounts": trend_amounts,
            "orders": trend_orders,
        },
        "top_items": top_items,
        "recent_orders": [_serialize_order(order) for order in recent],
    }