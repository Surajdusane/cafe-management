import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal, init_db
from app.main import app
from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.purchase import Purchase, PurchaseItem
from app.models.supplier import Supplier

RUN_TAG = uuid.uuid4().hex[:6]


def N(base: str) -> str:
    return f"{base} #{RUN_TAG}"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def cleanup_tagged_rows():
    def purge():
        init_db()  # creates the purchases tables if this DB file predates Phase 10
        with SessionLocal() as db:
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


def _supplier(client, name: str) -> dict:
    return client.post("/api/suppliers", json={"name": N(name)}).json()["data"]


def _material(client, name: str, quantity: float = 0, price: float = 50.0) -> dict:
    return client.post(
        "/api/inventory/items",
        json={
            "name": N(name),
            "category": "Dairy",
            "unit": "Litre",
            "initial_quantity": quantity,
            "minimum_stock": 2,
            "purchase_price": price,
        },
    ).json()["data"]


def _payload(supplier_id: int, items: list[dict], **overrides) -> dict:
    payload = {"supplier_id": supplier_id, "items": items}
    payload.update(overrides)
    return payload


# ===================== Successful purchases =====================


def test_successful_purchase_with_server_calculated_totals(client):
    supplier = _supplier(client, "Gokul Dairy")
    milk = _material(client, "Milk", quantity=10, price=56.0)
    beans = _material(client, "Coffee Beans", quantity=5, price=800.0)

    response = client.post(
        "/api/purchases",
        json=_payload(
            supplier["id"],
            [
                {"inventory_item_id": milk["id"], "quantity": 2.5, "unit_cost": 56.0},
                {"inventory_item_id": beans["id"], "quantity": 1, "unit_cost": 799.99},
            ],
        ),
    )

    assert response.status_code == 201
    body = response.json()
    assert "PUR-" in body["message"]
    data = body["data"]

    # Purchase number derived from the id (ORD-style), zero-padded.
    assert data["purchase_number"] == f"PUR-{data['id']:04d}"
    assert data["supplier_id"] == supplier["id"]
    assert data["supplier_name"] == supplier["name"]  # snapshot for history
    assert data["purchase_date"] == date.today().isoformat()  # defaults to today

    line_totals = [item["line_total"] for item in data["items"]]
    assert line_totals == [140.0, 799.99]
    assert data["subtotal"] == round(140.0 + 799.99, 2)
    assert data["total"] == data["subtotal"]  # server is the source of truth
    assert data["payment_status"] == "Unpaid"
    assert data["item_count"] == 2


def test_explicit_date_and_paid_status_are_accepted(client):
    supplier = _supplier(client, "Paid Supplies")
    material = _material(client, "Sugar Bags")

    response = client.post(
        "/api/purchases",
        json=_payload(
            supplier["id"],
            [{"inventory_item_id": material["id"], "quantity": 4, "unit_cost": 40}],
            purchase_date="2026-08-01",
            payment_status="Paid",
            notes="Invoice INV-77",
        ),
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["purchase_date"] == "2026-08-01"
    assert data["payment_status"] == "Paid"
    assert data["notes"] == "Invoice INV-77"


def test_purchase_updates_inventory_and_writes_stock_history(client):
    supplier = _supplier(client, "Stocky Suppliers")
    milk = _material(client, "History Milk", quantity=10)

    created = client.post(
        "/api/purchases",
        json=_payload(
            supplier["id"], [{"inventory_item_id": milk["id"], "quantity": 4, "unit_cost": 56}]
        ),
    ).json()["data"]

    detail = client.get(f"/api/inventory/items/{milk['id']}").json()["data"]
    assert detail["current_quantity"] == 14  # 10 + 4

    newest = detail["transactions"][0]
    assert newest["transaction_type"] == "Stock In"
    assert newest["quantity"] == 4
    assert newest["balance_after"] == 14
    assert newest["note"] == f"Purchase {created['purchase_number']}"


def test_multiple_items_update_every_material(client):
    supplier = _supplier(client, "Multi Supplier")
    a = _material(client, "Flour Multi", quantity=1)
    b = _material(client, "Cheese Multi", quantity=2)
    c = _material(client, "Oil Multi", quantity=3)

    response = client.post(
        "/api/purchases",
        json=_payload(
            supplier["id"],
            [
                {"inventory_item_id": a["id"], "quantity": 5, "unit_cost": 40},
                {"inventory_item_id": b["id"], "quantity": 1.5, "unit_cost": 300},
                {"inventory_item_id": c["id"], "quantity": 6, "unit_cost": 150},
            ],
        ),
    )
    assert response.status_code == 201

    assert client.get(f"/api/inventory/items/{a['id']}").json()["data"]["current_quantity"] == 6
    assert client.get(f"/api/inventory/items/{b['id']}").json()["data"]["current_quantity"] == 3.5
    assert client.get(f"/api/inventory/items/{c['id']}").json()["data"]["current_quantity"] == 9


def test_total_calculation_rounding(client):
    supplier = _supplier(client, "Rounding Supplier")
    material = _material(client, "Rounding Material")

    data = client.post(
        "/api/purchases",
        json=_payload(
            supplier["id"],
            [{"inventory_item_id": material["id"], "quantity": 3.33341, "unit_cost": 10.558}],
        ),
    ).json()["data"]

    line = data["items"][0]
    assert line["quantity"] == 3.333  # quantities round to 3 decimals
    assert line["unit_cost"] == 10.56  # money rounds to 2
    assert line["line_total"] == 35.2  # server multiplies the rounded inputs
    assert data["total"] == 35.2


# ===================== Invalid purchases =====================


def test_unknown_supplier_rejected_and_nothing_changes(client):
    material = _material(client, "No Supplier Item", quantity=8)
    before = len(client.get("/api/purchases").json()["data"]["items"])

    response = client.post(
        "/api/purchases",
        json=_payload(999999, [{"inventory_item_id": material["id"], "quantity": 1, "unit_cost": 5}]),
    )

    assert response.status_code == 404
    assert "Supplier" in response.json()["message"]
    assert len(client.get("/api/purchases").json()["data"]["items"]) == before  # nothing created
    assert (
        client.get(f"/api/inventory/items/{material['id']}").json()["data"]["current_quantity"] == 8
    )


def test_unknown_material_rejected_atomically(client):
    """One bad line must roll back the whole purchase — stock and rows."""
    supplier = _supplier(client, "Atomic Supplier")
    good = _material(client, "Atomic Milk", quantity=7)

    response = client.post(
        "/api/purchases",
        json=_payload(
            supplier["id"],
            [
                {"inventory_item_id": good["id"], "quantity": 3, "unit_cost": 50},
                {"inventory_item_id": 999999, "quantity": 1, "unit_cost": 9},
            ],
        ),
    )

    assert response.status_code == 404
    # Atomicity: the valid line's stock never moved either.
    assert client.get(f"/api/inventory/items/{good['id']}").json()["data"]["current_quantity"] == 7
    with SessionLocal() as db:
        count = db.scalar(select(Purchase.id).where(Purchase.supplier_id == supplier["id"]))
    assert count is None  # no purchase header was left behind


def test_inactive_material_rejected(client):
    supplier = _supplier(client, "Inactive Buyer")
    material = _material(client, "Retired Material", quantity=4)
    client.put(
        f"/api/inventory/items/{material['id']}",
        json={
            "name": material["name"],
            "category": "Dairy",
            "unit": "Litre",
            "minimum_stock": 2,
            "purchase_price": 50,
            "is_active": False,
        },
    )

    response = client.post(
        "/api/purchases",
        json=_payload(supplier["id"], [{"inventory_item_id": material["id"], "quantity": 1, "unit_cost": 5}]),
    )

    assert response.status_code == 409
    assert "inactive" in response.json()["message"]


@pytest.mark.parametrize(
    "items",
    [
        [],  # empty cart
        [{"inventory_item_id": 1, "quantity": 0, "unit_cost": 5}],  # zero quantity
        [{"inventory_item_id": 1, "quantity": -2, "unit_cost": 5}],  # negative quantity
        [{"inventory_item_id": 1, "quantity": 1, "unit_cost": -0.01}],  # negative cost
        [  # same material twice
            {"inventory_item_id": 1, "quantity": 1, "unit_cost": 5},
            {"inventory_item_id": 1, "quantity": 2, "unit_cost": 5},
        ],
        [{"quantity": 1, "unit_cost": 5}],  # missing material id
        [{"inventory_item_id": 1, "quantity": 1}],  # missing unit cost
    ],
)
def test_invalid_item_lists_rejected(client, items):
    # Body validation happens before the endpoint runs, so no real supplier is
    # needed — an invalid body must fail with 422 without touching the database.
    response = client.post("/api/purchases", json=_payload(999999, items))
    assert response.status_code == 422
    assert response.json()["success"] is False


def test_invalid_scalar_values_rejected(client):
    # Same idea: every body below has exactly one invalid field, so FastAPI's
    # validation layer rejects it with 422 before any database work.
    base_items = [{"inventory_item_id": 1, "quantity": 1, "unit_cost": 5}]

    cases = [
        {"supplier_id": 0},  # below minimum
        {"supplier_id": True},  # boolean must not pass as an id
        {"supplier_id": "abc"},
        {"purchase_date": "not-a-date"},
        {"payment_status": "Maybe"},  # not one of Unpaid/Paid
        {"notes": "x" * 256},
    ]
    for override in cases:
        payload = {**_payload(1, base_items), **override}
        response = client.post("/api/purchases", json=payload)
        assert response.status_code == 422, f"Expected 422 for {override}"

    bool_qty = _payload(1, [{"inventory_item_id": 1, "quantity": True, "unit_cost": 5}])
    assert client.post("/api/purchases", json=bool_qty).status_code == 422


# ===================== History, filters and payment status =====================


def test_list_filters_search_supplier_payment_dates(client):
    supplier_a = _supplier(client, "Filter Foods")
    supplier_b = _supplier(client, "Other Foods")
    mat_a = _material(client, "Filter Material A")
    mat_b = _material(client, "Filter Material B")

    tagged = client.post(
        "/api/purchases",
        json=_payload(supplier_a["id"], [{"inventory_item_id": mat_a["id"], "quantity": 2, "unit_cost": 30}]),
    ).json()["data"]
    old = client.post(
        "/api/purchases",
        json=_payload(
            supplier_b["id"],
            [{"inventory_item_id": mat_b["id"], "quantity": 1, "unit_cost": 100}],
            purchase_date=(date.today() - timedelta(days=10)).isoformat(),
        ),
    ).json()["data"]

    # search by number fragment…
    by_number = client.get("/api/purchases", params={"search": tagged["purchase_number"]}).json()
    assert [p["id"] for p in by_number["data"]["items"]] == [tagged["id"]]
    # …and by supplier-name fragment
    by_supplier_name = client.get("/api/purchases", params={"search": N("Filter Foods")}).json()
    assert by_supplier_name["data"]["count"] >= 1
    assert tagged["id"] in [p["id"] for p in by_supplier_name["data"]["items"]]

    by_supplier = client.get("/api/purchases", params={"supplier_id": supplier_a["id"]}).json()
    assert [p["id"] for p in by_supplier["data"]["items"]] == [tagged["id"]]

    # date range that only covers the older purchase (the shared dev database
    # may hold rows from other runs, so assert on this run's tagged ids only)
    end = date.today() - timedelta(days=5)
    ranged = client.get("/api/purchases", params={"end_date": end.isoformat()})
    ranged_ids = [p["id"] for p in ranged.json()["data"]["items"]]
    assert old["id"] in ranged_ids
    assert tagged["id"] not in ranged_ids

    # payment filter — everything starts Unpaid
    unpaid = client.get("/api/purchases", params={"payment_status": "Unpaid"}).json()["data"]["items"]
    assert tagged["id"] in [p["id"] for p in unpaid]

    summary = client.get("/api/purchases", params={"search": tagged["purchase_number"]}).json()["data"]["summary"]
    assert summary["count"] == 1
    assert summary["total_amount"] == 60.0
    assert summary["unpaid_count"] == 1
    assert summary["unpaid_amount"] == 60.0


def test_read_detail_and_missing_id(client):
    supplier = _supplier(client, "Detail Supplier")
    material = _material(client, "Detail Material")
    created = client.post(
        "/api/purchases",
        json=_payload(supplier["id"], [{"inventory_item_id": material["id"], "quantity": 2, "unit_cost": 12}]),
    ).json()["data"]

    detail = client.get(f"/api/purchases/{created['id']}")
    assert detail.status_code == 200
    body = detail.json()["data"]
    assert body["purchase_number"] == created["purchase_number"]
    assert len(body["items"]) == 1
    assert body["items"][0]["item_name"] == material["name"]  # snapshot stored

    missing = client.get("/api/purchases/999999")
    assert missing.status_code == 404
    assert missing.json()["success"] is False


def test_payment_status_toggle(client):
    supplier = _supplier(client, "Payment Supplier")
    material = _material(client, "Payment Material")
    created = client.post(
        "/api/purchases",
        json=_payload(supplier["id"], [{"inventory_item_id": material["id"], "quantity": 1, "unit_cost": 20}]),
    ).json()["data"]

    paid = client.put(
        f"/api/purchases/{created['id']}/payment-status", json={"payment_status": "Paid"}
    )
    assert paid.status_code == 200
    assert paid.json()["data"]["payment_status"] == "Paid"

    reverted = client.put(
        f"/api/purchases/{created['id']}/payment-status", json={"payment_status": "Unpaid"}
    )
    assert reverted.json()["data"]["payment_status"] == "Unpaid"

    bad = client.put(
        f"/api/purchases/{created['id']}/payment-status", json={"payment_status": "Pending"}
    )
    assert bad.status_code == 422

    missing = client.put("/api/purchases/999999/payment-status", json={"payment_status": "Paid"})
    assert missing.status_code == 404


def test_deleting_supplier_keeps_purchase_history(client):
    supplier = _supplier(client, "Vanishing Supplier")
    material = _material(client, "Vanishing Material")
    created = client.post(
        "/api/purchases",
        json=_payload(supplier["id"], [{"inventory_item_id": material["id"], "quantity": 3, "unit_cost": 10}]),
    ).json()["data"]

    deleted = client.delete(f"/api/suppliers/{supplier['id']}")
    assert deleted.status_code == 200

    detail = client.get(f"/api/purchases/{created['id']}").json()["data"]
    assert detail["supplier_id"] is None  # link cleared…
    assert detail["supplier_name"] == supplier["name"]  # …snapshot keeps history readable
    assert detail["total"] == 30.0  # money untouched


def test_purchases_persisted_in_sqlite(client):
    supplier = _supplier(client, "Persist Supplier")
    material = _material(client, "Persist Material", quantity=2)
    created = client.post(
        "/api/purchases",
        json=_payload(supplier["id"], [{"inventory_item_id": material["id"], "quantity": 2.5, "unit_cost": 40}]),
    ).json()["data"]

    with SessionLocal() as db:
        row = db.get(Purchase, created["id"])
        assert row is not None
        assert row.purchase_number == created["purchase_number"]
        assert row.total == 100.0
        lines = db.scalars(select(PurchaseItem).where(PurchaseItem.purchase_id == row.id)).all()
        assert len(lines) == 1
        assert lines[0].quantity == 2.5
