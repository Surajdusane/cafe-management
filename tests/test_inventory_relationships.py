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
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value
    if "#" not in payload.get("name", ""):
        payload["name"] = N(payload["name"])
    return client.post("/api/inventory/items", json=payload)


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "   "},
        {"category": ""},
        {"category": None},
        {"unit": "Bucket"},
        {"unit": None},
        {"initial_quantity": -1},
        {"minimum_stock": -2},
        {"purchase_price": -0.5},
        {"initial_quantity": "ten"},
        {"minimum_stock": True},
        {"supplier_id": -3},
        {"supplier_id": 0},
        {"notes": "x" * 256},
    ],
    ids=[
        "blank-name",
        "blank-category",
        "missing-category",
        "unknown-unit",
        "missing-unit",
        "negative-initial-qty",
        "negative-min-stock",
        "negative-price",
        "text-quantity",
        "boolean-number",
        "negative-supplier-id",
        "zero-supplier-id",
        "notes-too-long",
    ],
)
def test_create_with_invalid_data_fails_validation(client, changes):
    payload = {**VALID_ITEM}
    for key, value in changes.items():
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value

    response = client.post("/api/inventory/items", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert len(body.get("errors", [])) > 0


@pytest.fixture(scope="module")
def salt_item(client):
    """One material shared by every invalid-movement case (they never mutate it)."""
    response = _create_item(client, name=N("Salt"), initial_quantity=10)
    assert response.status_code == 201
    return response.json()["data"]


@pytest.mark.parametrize(
    "payload",
    [
        {"transaction_type": "Top-up", "quantity": 1},
        {"transaction_type": "", "quantity": 1},
        {"quantity": 1},  # type missing entirely
        {"transaction_type": "Stock In", "quantity": 0},
        {"transaction_type": "Stock In", "quantity": -5},
        {"transaction_type": "Stock Out", "quantity": 0},
        {"transaction_type": "Adjustment", "quantity": -1},
        {"transaction_type": "Adjustment", "quantity": True},
        {"transaction_type": "Stock In", "quantity": 1, "note": "x" * 201},
    ],
    ids=[
        "bad-type-topup",
        "empty-type",
        "missing-type",
        "zero-stock-in",
        "negative-stock-in",
        "zero-stock-out",
        "negative-adjustment",
        "boolean-adjustment",
        "note-too-long",
    ],
)
def test_invalid_movements_fail_validation(client, salt_item, payload):
    response = client.post(f"/api/inventory/items/{salt_item['id']}/stock", json=payload)

    assert response.status_code == 422
    assert response.json()["success"] is False


def test_unknown_supplier_on_create_is_404(client):
    response = _create_item(client, name=N("Ghost Goods"), supplier_id=999999)

    assert response.status_code == 404
    assert "Create it first" in response.json()["message"]


def test_unknown_supplier_on_update_is_404(client):
    created = _create_item(client, name=N("Lemons"), initial_quantity=2).json()["data"]
    response = client.put(
        f"/api/inventory/items/{created['id']}",
        json={**{k: v for k, v in created.items() if k != "id"}, "supplier_id": 999999},
    )

    assert response.status_code == 404


def test_unknown_item_404_on_all_routes(client):
    assert client.get("/api/inventory/items/999999").status_code == 404
    assert (
        client.put(
            "/api/inventory/items/999999",
            json={"name": N("Nope"), "category": "X", "unit": "Kg"},
        ).status_code
        == 404
    )
    assert client.delete("/api/inventory/items/999999").status_code == 404
    stock = client.post("/api/inventory/items/999999/stock", json={"transaction_type": "Stock In", "quantity": 1})
    assert stock.status_code == 404


def test_delete_item_removes_history_rows(client):
    created = _create_item(client, name=N("Cocoa"), initial_quantity=7).json()["data"]
    client.post(f"/api/inventory/items/{created['id']}/stock", json={"transaction_type": "Stock Out", "quantity": 2})

    response = client.delete(f"/api/inventory/items/{created['id']}")
    assert response.status_code == 200
    assert "deleted" in response.json()["message"]

    with SessionLocal() as db:
        remaining = db.scalar(
            select(func.count(InventoryTransaction.id)).where(InventoryTransaction.item_id == created["id"])
        )
    assert remaining == 0
    assert client.get(f"/api/inventory/items/{created['id']}").status_code == 404


def test_deleting_supplier_clears_material_link_but_keeps_stock(client):
    supplier_row = client.post("/api/suppliers", json={"name": N("Vanishing Vendor")}).json()["data"]
    created = _create_item(
        client, name=N("Yoghurt"), initial_quantity=9, supplier_id=supplier_row["id"]
    ).json()["data"]

    deleted = client.delete(f"/api/suppliers/{supplier_row['id']}")
    assert deleted.status_code == 200

    detail = client.get(f"/api/inventory/items/{created['id']}")
    assert detail.status_code == 200
    data = detail.json()["data"]
    assert data["supplier_id"] is None
    assert data["supplier"] is None
    assert data["current_quantity"] == 9  # stock and history untouched


def test_invalid_item_id_in_path_is_422(client):
    response = client.get("/api/inventory/items/not-a-number")

    assert response.status_code == 422


def test_persisted_in_sqlite_with_exact_values(client):
    created = _create_item(
        client, name=N("Basmati"), unit="Kg", initial_quantity=15.5, minimum_stock=3, purchase_price=120.75
    ).json()["data"]

    with SessionLocal() as db:
        row = db.get(InventoryItem, created["id"])
        assert row is not None
        assert row.name == N("Basmati")
        assert round(row.current_quantity, 3) == 15.5
        assert round(row.purchase_price, 2) == 120.75
