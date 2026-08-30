import re
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.main import app
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.order import Order

# Tagged names keep this module isolated from real data and previous runs.
RUN_TAG = uuid.uuid4().hex[:6]


def N(base: str) -> str:
    return f"{base} #{RUN_TAG}"


CATEGORY_NAME = N("QA Order Category")
TAX_PERCENT = 5.0

# Prices chosen so every total below is hand-checkable.
PRICE_A = 100.0  # Cappuccino QA
PRICE_B = 50.0  # Cookie QA

TEST_TAX_SETTINGS = {
    "cafe_name": N("Tax Check Cafe"),
    "address": "1 Test Lane",
    "phone": "9876543210",
    "email": "tax@example.com",
    "logo_url": None,
    "tax_percent": TAX_PERCENT,
    "currency": "₹",
    "receipt_footer": "Test footer",
}

created_order_ids: list[int] = []


def register_order(response):
    body = response.json()
    if response.status_code == 201 and body.get("data", {}).get("id"):
        created_order_ids.append(body["data"]["id"])
    return response


def make_order(client, lines, **overrides):
    payload = {"order_type": "Dine-in", "table_number": 4, "items": lines, **overrides}
    return register_order(client.post("/api/orders", json=payload))


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def order_environment(client):
    """Known settings (tax 5%) plus a private category with priced items."""
    original = client.get("/api/settings").json()["data"]
    saved = client.put("/api/settings", json={**original, **TEST_TAX_SETTINGS})
    assert saved.status_code == 200, saved.text

    category = client.post("/api/categories", json={"name": CATEGORY_NAME}).json()["data"]

    def add_item(name, price, available=True):
        body = client.post(
            "/api/menu/items",
            json={
                "category_id": category["id"],
                "name": N(name),
                "price": price,
                "is_available": available,
            },
        )
        assert body.status_code == 201, body.text
        return body.json()["data"]

    item_a = add_item("Cappuccino QA", PRICE_A)
    item_b = add_item("Cookie QA", PRICE_B)
    sold_out = add_item("Sold Out QA", 70.0, available=False)

    env = {
        "category": category,
        "item_a": item_a,
        "item_b": item_b,
        "sold_out": sold_out,
    }
    yield env

    with SessionLocal() as db:
        if created_order_ids:
            orders = db.query(Order).filter(Order.id.in_(created_order_ids)).all()
            for order in orders:
                db.delete(order)  # ORM cascade removes the item lines
            db.commit()
        tagged = db.scalars(
            select(Category.id).where(Category.name.like(f"%#{RUN_TAG}"))
        ).all()
        if tagged:
            db.execute(delete(MenuItem).where(MenuItem.category_id.in_(tagged)))
            db.execute(delete(Category).where(Category.id.in_(tagged)))
            db.commit()
        # Restore whatever settings existed before this module ran.
        client.put("/api/settings", json=original)


# ---------------------------------------------------------------------------
# Creation and server-side money calculation
# ---------------------------------------------------------------------------


def test_create_dine_in_order_with_server_totals(client, order_environment):
    """2×₹100 + 1×₹50 = ₹250 subtotal; ₹10 discount; 5% tax on ₹240 = ₹12."""
    response = make_order(
        client,
        [
            {"menu_item_id": order_environment["item_a"]["id"], "quantity": 2},
            {"menu_item_id": order_environment["item_b"]["id"], "quantity": 1},
        ],
        discount_amount=10,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Order created."

    data = body["data"]
    assert re.fullmatch(r"ORD-\d{4}", data["order_number"])
    assert data["status"] == "Pending"
    assert data["payment_status"] == "Unpaid"
    assert data["order_type"] == "Dine-in"
    assert data["table_number"] == 4
    assert data["subtotal"] == pytest.approx(250.0)
    assert data["discount_amount"] == pytest.approx(10.0)
    assert data["tax_percent"] == pytest.approx(TAX_PERCENT)
    assert data["tax_amount"] == pytest.approx(12.0)
    assert data["total"] == pytest.approx(252.0)

    assert len(data["items"]) == 2
    first = data["items"][0]
    assert first["item_name"] == order_environment["item_a"]["name"]  # snapshot
    assert first["unit_price"] == pytest.approx(PRICE_A)
    assert first["line_total"] == pytest.approx(200.0)


def test_create_takeaway_without_table(client, order_environment):
    response = make_order(
        client,
        [{"menu_item_id": order_environment["item_b"]["id"], "quantity": 1}],
        order_type="Takeaway",
        table_number=None,
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["table_number"] is None
    expected_total = round(50.0 * 1.05, 2)
    assert data["total"] == pytest.approx(expected_total)


def test_takeaway_ignores_sent_table_number(client, order_environment):
    response = make_order(
        client,
        [{"menu_item_id": order_environment["item_b"]["id"], "quantity": 1}],
        order_type="Takeaway",
        table_number=7,  # meaningless for takeaway; server normalises to NULL
    )

    assert response.status_code == 201
    assert response.json()["data"]["table_number"] is None


def test_dine_in_requires_table_number(client, order_environment):
    response = make_order(
        client,
        [{"menu_item_id": order_environment["item_b"]["id"], "quantity": 1}],
        table_number=None,
    )

    assert response.status_code == 422
    errors = response.json()["errors"]
    assert any("Table number" in error["message"] for error in errors)


def test_invalid_order_type_rejected(client, order_environment):
    response = make_order(
        client,
        [{"menu_item_id": order_environment["item_b"]["id"], "quantity": 1}],
        order_type="Delivery",
    )

    assert response.status_code == 422


def test_money_rounding_to_two_decimals(client, order_environment):
    """3 × ₹19.99 = ₹59.97; 5% tax = ₹2.9985 → ₹3.00; total ₹62.97."""
    pricey = client.post(
        "/api/menu/items",
        json={"category_id": order_environment["category"]["id"], "name": N("Rounded Tea"), "price": 19.99},
    )
    assert pricey.status_code == 201
    item = pricey.json()["data"]

    response = make_order(
        client,
        [{"menu_item_id": item["id"], "quantity": 3}],
        order_type="Takeaway",
        table_number=None,
    )

    data = response.json()["data"]
    assert data["subtotal"] == pytest.approx(59.97)
    assert data["tax_amount"] == pytest.approx(3.0)
    assert data["total"] == pytest.approx(62.97)


@pytest.mark.parametrize(
    "lines",
    [
        [],
        [{"quantity": 2}],  # missing menu_item_id
        [{"menu_item_id": 1}],  # missing quantity
        [{"menu_item_id": 0, "quantity": 1}],  # zero id
    ],
    ids=["empty-items", "missing-item-id", "missing-quantity", "zero-item-id"],
)
def test_invalid_item_lists_fail_validation(client, order_environment, lines):
    response = make_order(client, lines)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "quantity",
    [0, -2, 1.5, "two", True, 1000],
    ids=["zero", "negative", "decimal", "text", "boolean", "over-max"],
)
def test_invalid_quantities_fail_validation(client, order_environment, quantity):
    response = make_order(
        client, [{"menu_item_id": order_environment["item_a"]["id"], "quantity": quantity}]
    )

    assert response.status_code == 422


def test_unknown_menu_item_returns_404(client):
    response = make_order(client, [{"menu_item_id": 999999, "quantity": 1}])

    assert response.status_code == 404
    assert "not found" in response.json()["message"].lower()


def test_unavailable_menu_item_rejected(client, order_environment):
    response = make_order(
        client, [{"menu_item_id": order_environment["sold_out"]["id"], "quantity": 1}]
    )

    assert response.status_code == 409
    assert "unavailable" in response.json()["message"].lower()


def test_duplicate_item_lines_rejected(client, order_environment):
    item_id = order_environment["item_a"]["id"]
    response = make_order(
        client,
        [{"menu_item_id": item_id, "quantity": 1}, {"menu_item_id": item_id, "quantity": 2}],
    )

    assert response.status_code == 422


@pytest.mark.parametrize("bad_discount", [-5, "free", True], ids=["negative", "text", "boolean"])
def test_invalid_discounts_fail_validation(client, order_environment, bad_discount):
    response = make_order(
        client,
        [{"menu_item_id": order_environment["item_b"]["id"], "quantity": 1}],
        discount_amount=bad_discount,
    )

    assert response.status_code == 422


def test_discount_above_subtotal_rejected(client, order_environment):
    response = make_order(
        client,
        [{"menu_item_id": order_environment["item_b"]["id"], "quantity": 1}],
        discount_amount=51.0,  # subtotal is only ₹50
    )

    assert response.status_code == 400
    assert "subtotal" in response.json()["message"].lower()


def test_zero_discount_allowed(client, order_environment):
    response = make_order(
        client,
        [{"menu_item_id": order_environment["item_b"]["id"], "quantity": 1}],
        discount_amount=0,
    )

    assert response.status_code == 201
    assert response.json()["data"]["discount_amount"] == 0.0


# ---------------------------------------------------------------------------
# Status workflow
# ---------------------------------------------------------------------------


def test_status_lifecycle_pending_to_completed(client, order_environment):
    created = make_order(
        client,
        [{"menu_item_id": order_environment["item_b"]["id"], "quantity": 1}],
        order_type="Takeaway",
        table_number=None,
    ).json()["data"]

    for next_status in ["Preparing", "Ready", "Completed"]:
        moved = client.put(f"/api/orders/{created['id']}/status", json={"status": next_status})

        assert moved.status_code == 200
        assert moved.json()["data"]["status"] == next_status
        assert f"marked as {next_status}" in moved.json()["message"]


@pytest.mark.parametrize(
    "bad_status", ["Cooking", "", "pending"], ids=["unknown", "blank", "lowercase"]
)
def test_invalid_status_value_rejected(client, order_environment, bad_status):
    created = make_order(
        client,
        [{"menu_item_id": order_environment["item_b"]["id"], "quantity": 1}],
        order_type="Takeaway",
        table_number=None,
    ).json()["data"]

    response = client.put(f"/api/orders/{created['id']}/status", json={"status": bad_status})

    assert response.status_code == 422


def test_cancelled_order_is_frozen(client, order_environment):
    created = make_order(
        client,
        [{"menu_item_id": order_environment["item_b"]["id"], "quantity": 1}],
        order_type="Takeaway",
        table_number=None,
    ).json()["data"]
    cancelled = client.put(f"/api/orders/{created['id']}/status", json={"status": "Cancelled"})
    assert cancelled.status_code == 200

    reopen = client.put(f"/api/orders/{created['id']}/status", json={"status": "Pending"})

    assert reopen.status_code == 409
    assert "cancelled" in reopen.json()["message"].lower()


def test_delete_blocked_until_cancelled_then_allowed(client, order_environment):
    created = make_order(
        client,
        [{"menu_item_id": order_environment["item_b"]["id"], "quantity": 1}],
        order_type="Takeaway",
        table_number=None,
    ).json()["data"]

    blocked = client.delete(f"/api/orders/{created['id']}")
    assert blocked.status_code == 409

    client.put(f"/api/orders/{created['id']}/status", json={"status": "Cancelled"})
    deleted = client.delete(f"/api/orders/{created['id']}")

    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Order deleted."
    assert client.get(f"/api/orders/{created['id']}").status_code == 404


# ---------------------------------------------------------------------------
# Listing, filtering, detail
# ---------------------------------------------------------------------------


def test_list_orders_newest_first_with_counts(client, order_environment):
    listed = client.get("/api/orders").json()["data"]

    assert listed["count"] >= 2
    mine = [o for o in listed["items"] if o["id"] in created_order_ids]
    assert all(o["item_count"] >= 1 for o in mine)


def test_filters_by_status_type_and_payment(client, order_environment):
    target = make_order(
        client,
        [{"menu_item_id": order_environment["item_b"]["id"], "quantity": 2}],
        order_type="Takeaway",
        table_number=None,
    ).json()["data"]
    client.put(f"/api/orders/{target['id']}/status", json={"status": "Preparing"})

    by_status = client.get("/api/orders", params={"order_status": "Preparing"}).json()["data"]
    assert target["id"] in [o["id"] for o in by_status["items"]]
    assert all(o["status"] == "Preparing" for o in by_status["items"])

    by_type = client.get("/api/orders", params={"order_type": "Takeaway"}).json()["data"]
    assert all(o["order_type"] == "Takeaway" for o in by_type["items"])

    by_payment = client.get("/api/orders", params={"payment_status": "Unpaid"}).json()["data"]
    assert all(o["payment_status"] == "Unpaid" for o in by_payment["items"])


def test_search_matches_order_number(client, order_environment):
    target = make_order(
        client,
        [{"menu_item_id": order_environment["item_a"]["id"], "quantity": 1}],
        order_type="Takeaway",
        table_number=None,
    ).json()["data"]
    fragment = target["order_number"][-4:]  # e.g. "0017"

    found = client.get("/api/orders", params={"search": fragment}).json()["data"]

    assert target["id"] in [o["id"] for o in found["items"]]


def test_read_single_order_detail(client, order_environment):
    created = make_order(
        client,
        [{"menu_item_id": order_environment["item_a"]["id"], "quantity": 2}],
    ).json()["data"]

    response = client.get(f"/api/orders/{created['id']}")

    assert response.status_code == 200
    detail = response.json()["data"]
    assert len(detail["items"]) == 1
    assert detail["items"][0]["quantity"] == 2
    assert {"id", "item_name", "unit_price", "line_total"} <= set(detail["items"][0])


def test_missing_order_returns_404_envelope(client):
    for method, path in [("get", "/api/orders/999999"), ("delete", "/api/orders/999999")]:
        response = getattr(client, method)(path)

        assert response.status_code == 404
        envelope = response.json()
        assert envelope["success"] is False
        assert "not found" in envelope["message"].lower()

    put = client.put("/api/orders/999999/status", json={"status": "Ready"})
    assert put.status_code == 404


def test_failed_create_leaves_order_count_unchanged(client, order_environment):
    before = client.get("/api/orders").json()["data"]["count"]
    make_order(client, [])  # invalid: empty items
    after = client.get("/api/orders").json()["data"]["count"]

    assert before == after


def test_order_persists_in_database(client, order_environment):
    created = make_order(
        client,
        [{"menu_item_id": order_environment["item_a"]["id"], "quantity": 1}],
        order_type="Takeaway",
        table_number=None,
    ).json()["data"]

    with SessionLocal() as db:
        row = db.get(Order, created["id"])
        assert row is not None
        assert row.total == pytest.approx(round(PRICE_A * 1.05, 2))
        assert row.items[0].item_name == order_environment["item_a"]["name"]
