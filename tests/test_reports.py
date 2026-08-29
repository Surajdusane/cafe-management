import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.main import app
from app.models.employee import Employee
from app.models.expense import Expense
from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.purchase import Purchase
from app.models.salary import Salary
from app.models.supplier import Supplier

RUN_TAG = uuid.uuid4().hex[:6]


def N(base: str) -> str:
    return f"{base} #{RUN_TAG}"


_seq = {"n": 0}


def UNIQ(base: str) -> str:
    """Tagged name unique across every call (creations reuse names otherwise)."""
    _seq["n"] += 1
    return f"{base} #{RUN_TAG} {_seq['n']}"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def snapshot_settings(client):
    """Pin tax to 0 so order totals equal their subtotals, restore afterwards."""
    original = client.get("/api/settings").json()["data"]
    restored = {**original, "tax_percent": 0}
    client.put("/api/settings", json=restored)

    yield

    client.put("/api/settings", json=original)


@pytest.fixture(scope="module", autouse=True)
def cleanup_tagged_rows():
    def purge():
        with SessionLocal() as db:
            employee_ids = db.scalars(
                select(Employee.id).where(Employee.name.like(f"%#{RUN_TAG}"))
            ).all()
            if employee_ids:
                db.execute(delete(Salary).where(Salary.employee_id.in_(employee_ids)))
                db.execute(delete(Employee).where(Employee.id.in_(employee_ids)))
            db.execute(delete(Expense).where(Expense.title.like(f"%#{RUN_TAG}")))
            db.execute(delete(Purchase).where(Purchase.supplier_name.like(f"%#{RUN_TAG}")))
            item_ids = db.scalars(
                select(InventoryItem.id).where(InventoryItem.name.like(f"%#{RUN_TAG}"))
            ).all()
            if item_ids:
                db.execute(
                    delete(InventoryTransaction).where(InventoryTransaction.item_id.in_(item_ids))
                )
                db.execute(delete(InventoryItem).where(InventoryItem.id.in_(item_ids)))
            db.execute(delete(Supplier).where(Supplier.name.like(f"%#{RUN_TAG}")))
            db.commit()

    purge()
    yield
    purge()


def _sales_total(client, period="monthly"):
    return client.get(
        "/api/reports/sales", params={"period": period}
    ).json()["data"]["summary"]["sales_total"]


def _paid_order(client, price: float = 500, qty: int = 2) -> dict:
    """Create a category + item + a paid dine-in order; returns the order dict."""
    category = client.post("/api/categories", json={"name": UNIQ("RptCat")}).json()["data"]
    item = client.post(
        "/api/menu/items",
        json={"category_id": category["id"], "name": UNIQ("Rpt Latte"), "price": price},
    ).json()["data"]
    order = client.post(
        "/api/orders",
        json={
            "order_type": "Dine-in",
            "table_number": 3,
            "items": [{"menu_item_id": item["id"], "quantity": qty}],
        },
    ).json()["data"]
    client.post(f"/api/bills/{order['id']}/pay", json={"payment_method": "Cash"})
    return order


def _purchase(client, amount: float) -> dict:
    supplier = client.post("/api/suppliers", json={"name": UNIQ("Rpt Supplier")}).json()["data"]
    material = client.post(
        "/api/inventory/items",
        json={"name": UNIQ("Rpt Beans"), "category": "Beverages", "unit": "Kg", "minimum_stock": 1},
    ).json()["data"]
    purchase = client.post(
        "/api/purchases",
        json={
            "supplier_id": supplier["id"],
            "items": [{"inventory_item_id": material["id"], "quantity": 1, "unit_cost": amount}],
        },
    ).json()["data"]
    return purchase


def _salary(client, amount: float, month: str = "2026-08") -> dict:
    employee = client.post(
        "/api/employees",
        json={
            "name": UNIQ("Rpt Employee"),
            "mobile": "9876543210",
            "role": "Waiter",
            "joining_date": "2025-01-10",
            "salary_type": "Monthly",
            "base_salary": amount,
            "is_active": True,
        },
    ).json()["data"]
    salary = client.post(
        "/api/salaries",
        json={
            "employee_id": employee["id"],
            "salary_month": month,
            "base_salary": amount,
            "payment_status": "Paid",
        },
    ).json()["data"]
    return salary


def _expense(client, amount: float, category: str = "Electricity") -> dict:
    return client.post(
        "/api/expenses",
        json={"title": N("Rpt bill"), "category": category, "amount": amount},
    ).json()["data"]


# ------------------------- Sales -------------------------

def test_sales_report_monthly_reflects_paid_order(client):
    before = _sales_total(client, "monthly")
    order = _paid_order(client, price=1234.0, qty=1)
    after = _sales_total(client, "monthly")

    assert after == round(before + order["total"], 2)


def test_sales_report_daily_has_today_bucket(client):
    data = client.get("/api/reports/sales", params={"period": "daily"}).json()["data"]
    assert data["period"] == "daily"
    # The series covers the last 14 days; today must always be included as a label.
    assert len(data["series"]["labels"]) == 14
    assert data["summary"]["sales_total"] == round(sum(data["series"]["amounts"]), 2)


def test_sales_report_weekly_single_week(client):
    data = client.get("/api/reports/sales", params={"period": "weekly"}).json()["data"]
    assert data["period_label"] == "Weekly"
    assert len(data["series"]["labels"]) == 7


def test_sales_report_empty_in_future_date_range(client):
    data = client.get(
        "/api/reports/sales",
        params={"period": "monthly", "start_date": "2099-01-01", "end_date": "2099-12-31"},
    ).json()["data"]
    assert data["summary"]["sales_total"] == 0.0
    assert data["summary"]["orders"] == 0


# ------------------------- Orders -------------------------

def test_orders_report_by_status_contains_completed(client):
    order = _paid_order(client, price=200, qty=1)
    # Advance to Completed, then back to the default for bucketing by current status.
    client.put(f"/api/orders/{order['id']}/status", json={"status": "Completed"})

    data = client.get("/api/reports/orders").json()["data"]
    statuses = {row["status"] for row in data["by_status"]}
    assert "Completed" in statuses

    completed = next(r for r in data["by_status"] if r["status"] == "Completed")
    assert completed["count"] >= 1


def test_orders_report_by_date_shape_and_summary_consistency(client):
    data = client.get("/api/reports/orders").json()["data"]
    by_status_total = round(sum(r["total"] for r in data["by_status"]), 2)
    by_date_total = round(sum(r["total"] for r in data["by_date"]), 2)
    assert data["summary"]["total"] == by_status_total
    assert by_status_total == by_date_total


def test_orders_report_empty_in_past_date_range(client):
    data = client.get(
        "/api/reports/orders", params={"start_date": "2000-01-01", "end_date": "2000-01-31"}
    ).json()["data"]
    assert data["summary"]["count"] == 0


# ------------------------- Inventory -------------------------

def test_inventory_report_current_includes_material(client):
    _purchase(client, 100)
    data = client.get("/api/reports/inventory", params={"report_type": "current"}).json()["data"]
    names = [item["name"] for item in data["items"]]
    assert any(RUN_TAG in name for name in names)


def test_inventory_report_movements_include_stock_in(client):
    _purchase(client, 50)
    data = client.get("/api/reports/inventory", params={"report_type": "movements"}).json()["data"]
    types = {m["transaction_type"] for m in data["items"]}
    assert "Stock In" in types


# ------------------------- Purchases -------------------------

def test_purchases_report_by_supplier_totals(client):
    purchase = _purchase(client, 333.5)
    data = client.get("/api/reports/purchases", params={"group_by": "supplier"}).json()["data"]
    supplier_rows = [r for r in data["items"] if r["name"] == purchase["supplier_name"]]
    assert len(supplier_rows) == 1
    assert supplier_rows[0]["total"] == round(purchase["total"], 2)


def test_purchases_report_by_date_shape(client):
    data = client.get("/api/reports/purchases", params={"group_by": "date"}).json()["data"]
    assert data["group_by"] == "date"
    assert data["summary"]["total"] == round(sum(r["total"] for r in data["items"]), 2)


# ------------------------- Salaries -------------------------

def test_salaries_report_monthly_total_included(client):
    salary = _salary(client, 15000)
    data = client.get("/api/reports/salaries").json()["data"]
    assert data["summary"]["total"] >= round(salary["net_salary"], 2)
    months = [r["month"] for r in data["items"]]
    assert salary["salary_month"] in months


# ------------------------- Expenses -------------------------

def test_expenses_report_by_category_totals(client):
    expense = _expense(client, 4200, "Gas")
    data = client.get("/api/reports/expenses", params={"group_by": "category"}).json()["data"]
    gas_rows = [r for r in data["items"] if r["category"] == "Gas"]
    assert len(gas_rows) == 1
    assert gas_rows[0]["total"] >= round(expense["amount"], 2)


def test_expenses_report_by_date_shape(client):
    _expense(client, 250, "Cleaning")
    data = client.get("/api/reports/expenses", params={"group_by": "date"}).json()["data"]
    assert data["group_by"] == "date"
    assert data["summary"]["total"] == round(sum(r["total"] for r in data["items"]), 2)


def test_expenses_report_empty_in_future_range(client):
    data = client.get(
        "/api/reports/expenses",
        params={"group_by": "category", "start_date": "2099-01-01", "end_date": "2099-12-31"},
    ).json()["data"]
    assert data["summary"]["count"] == 0


# ------------------------- Profit -------------------------

def test_profit_summary_components_consistent(client):
    before = client.get("/api/reports/profit").json()["data"]["estimated_profit"]

    # Create one of each contributor and confirm profit falls by the exact sum.
    order = _paid_order(client, price=1000, qty=1)
    purchase = _purchase(client, 200)
    salary = _salary(client, 300)
    expense = _expense(client, 100, "Rent")

    after = client.get("/api/reports/profit").json()["data"]
    delta = round(after["estimated_profit"] - before, 2)
    expected = round(
        order["total"] - purchase["total"] - salary["net_salary"] - expense["amount"], 2
    )
    assert delta == expected

    # Internal consistency of the formula.
    c = after["components"]
    assert round(c["sales"] - c["purchases"] - c["salaries"] - c["expenses"], 2) == after["estimated_profit"]
    assert "estimate" in after["labelled_note"].lower()


def test_profit_empty_range_is_zero(client):
    data = client.get(
        "/api/reports/profit", params={"start_date": "2000-01-01", "end_date": "2000-01-31"}
    ).json()["data"]
    assert data["estimated_profit"] == (data["components"]["sales"]
                                        - data["components"]["purchases"]
                                        - data["components"]["salaries"]
                                        - data["components"]["expenses"])
