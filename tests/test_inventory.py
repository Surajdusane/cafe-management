import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.main import app
from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.supplier import Supplier

RUN_TAG = uuid.uuid4().hex[:6]


def N(base: str) -> str:
    return f"{base} #{RUN_TAG}"


VALID_ITEM = {
    "name": N("Milk"),
    "category": "Dairy",
    "unit": "Litre",
    "initial_quantity": 10,
    "minimum_stock": 2,
    "purchase_price": 56.0,
    "supplier_id": None,
    "is_active": True,
    "notes": None,
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def cleanup_tagged_rows():
    def purge():
        with SessionLocal() as db:
            item_ids = db.scalars(
                select(InventoryItem.id).where(InventoryItem.name.like(f"%#{RUN_TAG}"))
            ).all()
            if item_ids:
                db.execute(
                    delete(InventoryTransaction).where(InventoryTransaction.item_id.in_(item_ids))
                )
                db.execute(delete(InventoryItem).where(InventoryItem.id.in_(item_ids)))
            supplier_ids = db.scalars(
                select(Supplier.id).where(Supplier.name.like(f"%#{RUN_TAG}"))
            ).all()
            if supplier_ids:
                db.execute(delete(Supplier).where(Supplier.id.in_(supplier_ids)))
            db.commit()

    purge()
    yield
    purge()


def _create_item(client, **overrides):
    payload = {**VALID_ITEM}
    for key, value in overrides.items():
        if key == "name":
            payload[key] = value if value.startswith("x") or "#" in value else N(value)
        elif value is None:
            payload.pop(key, None)
        else:
            payload[key] = value
    return client.post("/api/inventory/items", json=payload)


def _stock_url(item_id: int) -> str:
    return f"/api/inventory/items/{item_id}/stock"


def test_create_with_opening_stock_writes_first_movement(client):
    response = _create_item(client, name=N("Milk"), initial_quantity=12.5)

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Raw material created."
    data = body["data"]
    assert data["current_quantity"] == 12.5
    assert data["unit"] == "Litre"
    assert data["is_low_stock"] is False
    assert len(data["transactions"]) == 1
    opening = data["transactions"][0]
    assert opening["transaction_type"] == "Stock In"
    assert opening["quantity"] == 12.5
    assert opening["balance_after"] == 12.5
    assert opening["note"] == "Opening stock"


def test_create_with_zero_opening_stock_has_no_movements(client):
    created = _create_item(client, name=N("Sugar"), initial_quantity=0).json()["data"]

    assert created["current_quantity"] == 0
    assert created["transactions"] == []


def test_create_defaults_and_rounding(client):
    created = _create_item(
        client,
        name=N("Choco Powder"),
        category="Beverages",
        unit="Gram",
        initial_quantity=1.0004,
        minimum_stock=250.0004,
        purchase_price=1.999,
    ).json()["data"]

    # Quantities round to 3 decimals; price to 2.
    assert created["current_quantity"] == 1.0
    assert created["minimum_stock"] == 250.0
    assert created["purchase_price"] == 2.0
    assert created["is_active"] is True


def test_duplicate_name_rejected_case_insensitive(client):
    first = _create_item(client, name=N("Tea Powder"))
    duplicate_same = _create_item(client, name=N("Tea Powder"))
    duplicate_case = _create_item(client, name=N("TEA POWDER"))

    assert first.status_code == 201
    assert duplicate_same.status_code == 409
    assert duplicate_case.status_code == 409


def test_update_keeps_stock_level_untouched(client):
    created = _create_item(client, name=N("Flour"), initial_quantity=8).json()["data"]
    response = client.put(
        f"/api/inventory/items/{created['id']}",
        json={
            "name": N("Flour"),
            "category": "Bakery",
            "unit": "Kg",
            "minimum_stock": 1,
            "purchase_price": 42,
            "is_active": True,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["current_quantity"] == 8  # PUT never touches the level
    assert data["category"] == "Bakery"


def test_stock_in_adds_units_and_history(client):
    created = _create_item(client, name=N("Coffee Beans"), initial_quantity=5).json()["data"]

    response = client.post(_stock_url(created["id"]), json={"transaction_type": "Stock In", "quantity": 2.5})

    assert response.status_code == 200
    body = response.json()
    assert "New balance" in body["message"]
    assert body["data"]["item"]["current_quantity"] == 7.5
    transaction = body["data"]["transaction"]
    assert transaction["transaction_type"] == "Stock In"
    assert transaction["quantity"] == 2.5
    assert transaction["balance_after"] == 7.5


def test_stock_out_reduces_units(client):
    created = _create_item(client, name=N("Butter"), initial_quantity=10).json()["data"]

    response = client.post(_stock_url(created["id"]), json={"transaction_type": "Stock Out", "quantity": 4})

    assert response.status_code == 200
    assert response.json()["data"]["item"]["current_quantity"] == 6


def test_insufficient_stock_rejected_atomically(client):
    created = _create_item(client, name=N("Cheese"), initial_quantity=3).json()["data"]

    response = client.post(_stock_url(created["id"]), json={"transaction_type": "Stock Out", "quantity": 5})

    assert response.status_code == 409
    assert "Not enough stock" in response.json()["message"]

    # Atomicity: failed movement changed nothing and left no history row.
    detail = client.get(f"/api/inventory/items/{created['id']}").json()["data"]
    assert detail["current_quantity"] == 3
    with SessionLocal() as db:
        count = db.scalar(
            select(func.count(InventoryTransaction.id)).where(
                InventoryTransaction.item_id == created["id"],
                InventoryTransaction.transaction_type == "Stock Out",
            )
        )
    assert count == 0


def test_adjustment_sets_absolute_level_zero_allowed(client):
    created = _create_item(client, name=N("Bread"), initial_quantity=20).json()["data"]

    response = client.post(
        _stock_url(created["id"]),
        json={"transaction_type": "Adjustment", "quantity": 14, "note": "Physical count"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["item"]["current_quantity"] == 14

    zero_allowed = client.post(_stock_url(created["id"]), json={"transaction_type": "Adjustment", "quantity": 0})
    assert zero_allowed.status_code == 200
    assert zero_allowed.json()["data"]["item"]["current_quantity"] == 0


def test_low_stock_flag_thresholds(client):
    created = _create_item(
        client, name=N("Veggies"), category="Vegetables", unit="Kg", initial_quantity=6, minimum_stock=5
    ).json()["data"]
    assert created["is_low_stock"] is False  # above the minimum

    at_min = client.post(_stock_url(created["id"]), json={"transaction_type": "Adjustment", "quantity": 5})
    assert at_min.json()["data"]["item"]["is_low_stock"] is True  # at minimum counts as low

    out = client.post(_stock_url(created["id"]), json={"transaction_type": "Adjustment", "quantity": 0})
    assert out.json()["data"]["item"]["is_low_stock"] is True


def test_list_filters_and_summary(client):
    supplier_row = client.post("/api/suppliers", json={"name": N("Filter Foods")}).json()["data"]
    tagged = _create_item(
        client,
        name=N("Olives"),
        category="Groceries",
        initial_quantity=1,
        minimum_stock=4,
        supplier_id=supplier_row["id"],
    ).json()["data"]
    other = _create_item(client, name=N("Honey"), category="Groceries", initial_quantity=50, minimum_stock=2)
    assert other.status_code == 201

    by_search = client.get("/api/inventory/items", params={"search": N("Olives")}).json()
    assert [i["id"] for i in by_search["data"]["items"]] == [tagged["id"]]

    by_category = client.get("/api/inventory/items", params={"category": "Groceries"}).json()
    assert tagged["id"] in [i["id"] for i in by_category["data"]["items"]]

    by_supplier = client.get("/api/inventory/items", params={"supplier_id": supplier_row["id"]}).json()
    rows = by_supplier["data"]["items"]
    assert [i["id"] for i in rows] == [tagged["id"]]
    assert rows[0]["supplier"]["name"] == N("Filter Foods")

    low_only = client.get("/api/inventory/items", params={"low_stock_only": "true"}).json()
    assert tagged["id"] in [i["id"] for i in low_only["data"]["items"]]
    assert all(i["is_low_stock"] for i in low_only["data"]["items"])

    summary = low_only["data"]["summary"]
    assert summary["total_items"] >= 2
    assert summary["low_stock_items"] >= 1
    assert summary["total_suppliers"] >= 1


def test_transactions_history_endpoint_filters_newest_first(client):
    created = _create_item(client, name=N("Oil"), initial_quantity=30).json()["data"]
    client.post(_stock_url(created["id"]), json={"transaction_type": "Stock Out", "quantity": 5})
    client.post(_stock_url(created["id"]), json={"transaction_type": "Stock In", "quantity": 2})

    history = client.get("/api/inventory/transactions", params={"item_id": created["id"], "limit": 10}).json()
    rows = history["data"]["items"]
    assert len(rows) >= 3  # opening + out + in
    assert rows[0]["transaction_type"] == "Stock In"  # newest first
    assert rows[0]["item_name"] == created["name"]

    only_out = client.get(
        "/api/inventory/transactions",
        params={"item_id": created["id"], "transaction_type": "Stock Out"},
    ).json()
    assert all(row["transaction_type"] == "Stock Out" for row in only_out["data"]["items"])


def test_categories_endpoint_lists_distinct_sorted(client):
    _create_item(client, name=N("Saffron"), category="Spices")

    categories = client.get("/api/inventory/categories").json()["data"]["categories"]
    assert "Spices" in categories
    assert categories == sorted(categories)
