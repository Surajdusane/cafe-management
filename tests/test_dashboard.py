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
                db.execute(delete(Employee).where(Employee.id.in_(employee_ids)))
            db.execute(delete(Expense).where(Expense.title.like(f"%#{RUN_TAG}")))
            item_ids = db.scalars(
                select(InventoryItem.id).where(InventoryItem.name.like(f"%#{RUN_TAG}"))
            ).all()
            if item_ids:
                db.execute(
                    delete(InventoryTransaction).where(InventoryTransaction.item_id.in_(item_ids))
                )
                db.execute(delete(InventoryItem).where(InventoryItem.id.in_(item_ids)))
            db.commit()

    purge()
    yield
    purge()


# ------------------------- helpers -------------------------

def _dash(client) -> dict:
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    assert response.json()["success"] is True
    return response.json()["data"]


def _menu_item(client, name: str, *, available: bool = True, price: float = 200) -> dict:
    category = client.post(
        "/api/categories", json={"name": UNIQ("DashCat")}
    ).json()["data"]
    return client.post(
        "/api/menu/items",
        json={
            "category_id": category["id"],
            "name": name,
            "price": price,
            "is_available": available,
        },
    ).json()["data"]


def _order(client, item: dict, qty: int = 1, *, paid: bool = True) -> dict:
    order = client.post(
        "/api/orders",
        json={
            "order_type": "Takeaway",
            "items": [{"menu_item_id": item["id"], "quantity": qty}],
        },
    ).json()["data"]
    if paid:
        client.post(f"/api/bills/{order['id']}/pay", json={"payment_method": "Cash"})
    return order


def _material(client, name: str, minimum_stock: float = 1.0) -> dict:
    return client.post(
        "/api/inventory/items",
        json={"name": name, "category": "Dairy", "unit": "Litre", "minimum_stock": minimum_stock},
    ).json()["data"]


def _employee(client, name: str, *, is_active: bool = True) -> dict:
    return client.post(
        "/api/employees",
        json={
            "name": name,
            "mobile": "9876543210",
            "role": "Waiter",
            "joining_date": "2025-01-10",
            "salary_type": "Monthly",
            "base_salary": 10000,
            "is_active": is_active,
        },
    ).json()["data"]


def _expense(client, amount: float) -> dict:
    return client.post(
        "/api/expenses",
        json={"title": N("Dash bill"), "category": "Electricity", "amount": amount},
    ).json()["data"]


# ------------------------- shape -------------------------

def test_dashboard_envelope_and_shape(client):
    data = _dash(client)

    assert {"cafe", "date", "stats", "sales_trend", "top_items", "recent_orders"} <= set(data)
    assert data["date"] == date.today().isoformat()

    stats = data["stats"]
    for key in (
        "today_sales", "today_orders", "pending_orders", "unpaid_bills",
        "menu_items", "low_stock", "employees", "monthly_expenses",
    ):
        assert key in stats

    trend = data["sales_trend"]
    assert len(trend["labels"]) == 7
    assert len(trend["amounts"]) == 7
    assert len(trend["orders"]) == 7


def test_dashboard_cafe_branding_from_settings(client):
    original = client.get("/api/settings").json()["data"]
    client.put(
        "/api/settings",
        json={**original, "cafe_name": N("Dash Cafe"), "currency": "₹"},
    )
    try:
        data = _dash(client)
        assert data["cafe"]["name"] == N("Dash Cafe")
        assert data["cafe"]["currency"] == "₹"
    finally:
        client.put("/api/settings", json=original)


# ------------------------- today's numbers -------------------------

def test_dashboard_counts_paid_order(client):
    before_orders = _dash(client)["stats"]["today_orders"]
    before_sales = _dash(client)["stats"]["today_sales"]

    order = _order(client, _menu_item(client, UNIQ("Dash Latte"), price=375), qty=2)

    data = _dash(client)
    assert data["stats"]["today_orders"] == before_orders + 1
    assert data["stats"]["today_sales"] == round(before_sales + order["total"], 2)

    numbers = [row["order_number"] for row in data["recent_orders"]]
    assert order["order_number"] in numbers


def test_dashboard_pending_and_unpaid_are_not_sales(client):
    before_sales = _dash(client)["stats"]["today_sales"]
    before_pending = _dash(client)["stats"]["pending_orders"]
    before_unpaid = _dash(client)["stats"]["unpaid_bills"]

    order = _order(client, _menu_item(client, UNIQ("Dash Open")), qty=1, paid=False)

    data = _dash(client)
    assert data["stats"]["pending_orders"] == before_pending + 1
    assert data["stats"]["unpaid_bills"] == round(before_unpaid + order["total"], 2)
    # An unpaid order contributes to outstanding, never to today's sales.
    assert data["stats"]["today_sales"] == before_sales


# ------------------------- catalogue / staff -------------------------

def test_dashboard_menu_items_counts_available_only(client):
    before = _dash(client)["stats"]["menu_items"]

    _menu_item(client, UNIQ("Dash Avail"))
    assert _dash(client)["stats"]["menu_items"] == before + 1

    _menu_item(client, UNIQ("Dash Sold Out"), available=False)
    assert _dash(client)["stats"]["menu_items"] == before + 1


def test_dashboard_low_stock_count(client):
    before = _dash(client)["stats"]["low_stock"]
    _material(client, UNIQ("Dash Milk"), minimum_stock=5)  # 0 L stock ≤ min 5 → low
    assert _dash(client)["stats"]["low_stock"] == before + 1


def test_dashboard_employee_count(client):
    before = _dash(client)["stats"]["employees"]
    _employee(client, UNIQ("Dash Staff"))
    assert _dash(client)["stats"]["employees"] == before + 1

    _employee(client, UNIQ("Dash Leaver"), is_active=False)
    assert _dash(client)["stats"]["employees"] == before + 1


def test_dashboard_monthly_expenses(client):
    before = _dash(client)["stats"]["monthly_expenses"]
    expense = _expense(client, 1250.5)
    after = _dash(client)["stats"]["monthly_expenses"]
    assert after == round(before + expense["amount"], 2)


# ------------------------- trend / top sellers -------------------------

def test_dashboard_top_sellers_include_recent_orders(client):
    item = _menu_item(client, UNIQ("Dash Bestseller"), price=150)
    _order(client, item, qty=5)

    top = _dash(client)["top_items"]
    names = {row["name"] for row in top}
    quantities = {row["name"]: row["quantity"] for row in top}
    assert any(RUN_TAG in name for name in names)
    assert quantities[item["name"]] >= 5


def test_dashboard_empty_state_keys(client):
    data = _dash(client)
    # Shape stays stable even without any records at all (fresh/filtered state).
    assert isinstance(data["top_items"], list)
    assert isinstance(data["recent_orders"], list)