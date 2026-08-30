import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.main import app
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.order import Order

RUN_TAG = uuid.uuid4().hex[:6]


def N(base: str) -> str:
    return f"{base} #{RUN_TAG}"


CATEGORY_NAME = N("QA Bill Category")
TAX_PERCENT = 10.0

TEST_TAX_SETTINGS = {
    "cafe_name": N("Receipt Cafe"),
    "address": "9 Receipt Road",
    "phone": "9876543210",
    "email": "bill@example.com",
    "logo_url": None,
    "tax_percent": TAX_PERCENT,
    "currency": "₹",
    "receipt_footer": "Thank you — QA footer",
}

created_order_ids: list[int] = []


def register_order(response):
    body = response.json()
    if response.status_code == 201 and body.get("data", {}).get("id"):
        created_order_ids.append(body["data"]["id"])
    return response


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def bill_environment(client):
    """Tax 10% and one private item priced ₹150 for hand-checkable maths."""
    original = client.get("/api/settings").json()["data"]
    saved = client.put("/api/settings", json={**original, **TEST_TAX_SETTINGS})
    assert saved.status_code == 200, saved.text

    category = client.post("/api/categories", json={"name": CATEGORY_NAME}).json()["data"]
    item = client.post(
        "/api/menu/items",
        json={"category_id": category["id"], "name": N("Club Sandwich"), "price": 150.0},
    )
    assert item.status_code == 201, item.text

    env = {"category": category, "item": item.json()["data"]}
    yield env

    with SessionLocal() as db:
        if created_order_ids:
            orders = db.query(Order).filter(Order.id.in_(created_order_ids)).all()
            for order in orders:
                db.delete(order)
            db.commit()
        tagged = db.scalars(
            select(Category.id).where(Category.name.like(f"%#{RUN_TAG}"))
        ).all()
        if tagged:
            db.execute(delete(MenuItem).where(MenuItem.category_id.in_(tagged)))
            db.execute(delete(Category).where(Category.id.in_(tagged)))
            db.commit()
        client.put("/api/settings", json=original)


def _new_unpaid_order(client, env, quantity=2):
    """2 × ₹150 = ₹300 subtotal (no discount)."""
    return register_order(
        client.post(
            "/api/orders",
            json={
                "order_type": "Dine-in",
                "table_number": 2,
                "items": [{"menu_item_id": env["item"]["id"], "quantity": quantity}],
            },
        )
    ).json()["data"]


# ---------------------------------------------------------------------------
# Payment recording
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method", ["Cash", "UPI", "Card", "Other"], ids=["cash", "upi", "card", "other"]
)
def test_pay_bill_with_each_method(client, bill_environment, method):
    order = _new_unpaid_order(client, bill_environment)

    response = client.post(f"/api/bills/{order['id']}/pay", json={"payment_method": method})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["payment_status"] == "Paid"
    assert data["payment_method"] == method


def test_pay_sets_paid_at_timestamp(client, bill_environment):
    order = _new_unpaid_order(client, bill_environment)

    response = client.post(f"/api/bills/{order['id']}/pay", json={"payment_method": "UPI"})

    assert response.status_code == 200
    assert response.json()["data"]["paid_at"] is not None


def test_double_payment_rejected(client, bill_environment):
    order = _new_unpaid_order(client, bill_environment)
    client.post(f"/api/bills/{order['id']}/pay", json={"payment_method": "Cash"})

    again = client.post(f"/api/bills/{order['id']}/pay", json={"payment_method": "UPI"})

    assert again.status_code == 409
    assert "already paid" in again.json()["message"].lower()


def test_cancelled_bill_cannot_be_paid(client, bill_environment):
    order = _new_unpaid_order(client, bill_environment)
    client.put(f"/api/orders/{order['id']}/status", json={"status": "Cancelled"})

    response = client.post(f"/api/bills/{order['id']}/pay", json={"payment_method": "Cash"})

    assert response.status_code == 409
    assert "cancelled" in response.json()["message"].lower()


def test_paying_unknown_bill_returns_404(client):
    response = client.post("/api/bills/999999/pay", json={"payment_method": "Cash"})

    assert response.status_code == 404
    assert "not found" in response.json()["message"].lower()


@pytest.mark.parametrize("bad_method", ["Bitcoin", "", "cash"], ids=["unknown", "blank", "lowercase"])
def test_invalid_payment_method_rejected(client, bill_environment, bad_method):
    order = _new_unpaid_order(client, bill_environment)

    response = client.post(f"/api/bills/{order['id']}/pay", json={"payment_method": bad_method})

    assert response.status_code == 422


def test_paid_order_cannot_be_cancelled(client, bill_environment):
    """Refunds happen outside the system, so the API refuses to cancel paid orders."""
    order = _new_unpaid_order(client, bill_environment)
    client.post(f"/api/bills/{order['id']}/pay", json={"payment_method": "Card"})

    response = client.put(f"/api/orders/{order['id']}/status", json={"status": "Cancelled"})

    assert response.status_code == 409
    assert "paid" in response.json()["message"].lower()


# ---------------------------------------------------------------------------
# Billing maths
# ---------------------------------------------------------------------------


def test_tax_and_discount_calculation(client, bill_environment):
    """₹300 subtotal − ₹30 discount = ₹270 taxable; 10% tax = ₹27; total ₹297."""
    order = register_order(
        client.post(
            "/api/orders",
            json={
                "order_type": "Dine-in",
                "table_number": 2,
                "items": [{"menu_item_id": bill_environment["item"]["id"], "quantity": 2}],
                "discount_amount": 30,
            },
        )
    ).json()["data"]

    detail = client.get(f"/api/bills/{order['id']}").json()["data"]["bill"]

    assert detail["subtotal"] == pytest.approx(300.0)
    assert detail["discount_amount"] == pytest.approx(30.0)
    assert detail["tax_percent"] == pytest.approx(TAX_PERCENT)
    assert detail["tax_amount"] == pytest.approx(27.0)
    assert detail["total"] == pytest.approx(297.0)


def test_discounted_total_is_server_calculated(client, bill_environment):
    response = register_order(
        client.post(
            "/api/orders",
            json={
                "order_type": "Takeaway",
                "table_number": None,
                "items": [{"menu_item_id": bill_environment["item"]["id"], "quantity": 1}],
                "discount_amount": 25,
            },
        )
    )

    assert response.status_code == 201
    data = response.json()["data"]
    # ₹150 − ₹25 = ₹125 taxable → ₹12.50 tax → ₹137.50 total.
    assert data["total"] == pytest.approx(137.5)


# ---------------------------------------------------------------------------
# Bill list, filters and receipt payload
# ---------------------------------------------------------------------------


def test_bill_list_contains_summary_totals(client, bill_environment):
    listed = client.get("/api/bills").json()["data"]

    assert {"count", "billed_total", "collected_total", "outstanding_total"} <= set(listed["summary"])
    items = listed["items"]
    expected_billed = round(sum(item["total"] for item in items), 2)
    assert listed["summary"]["billed_total"] == pytest.approx(expected_billed)


def test_payment_filters_on_bill_list(client, bill_environment):
    order = _new_unpaid_order(client, bill_environment)
    client.post(f"/api/bills/{order['id']}/pay", json={"payment_method": "UPI"})

    paid = client.get("/api/bills", params={"payment_status": "Paid"}).json()["data"]
    unpaid = client.get("/api/bills", params={"payment_status": "Unpaid"}).json()["data"]
    by_upi = client.get("/api/bills", params={"payment_method": "UPI"}).json()["data"]

    assert all(b["payment_status"] == "Paid" for b in paid["items"])
    assert all(b["payment_status"] == "Unpaid" for b in unpaid["items"])
    assert order["id"] in [b["id"] for b in by_upi["items"]]
    assert all(b["payment_method"] == "UPI" for b in by_upi["items"])


def test_search_matches_bill_number(client, bill_environment):
    order = _new_unpaid_order(client, bill_environment)
    fragment = order["order_number"][-4:]

    found = client.get("/api/bills", params={"search": fragment}).json()["data"]

    assert order["id"] in [b["id"] for b in found["items"]]


def test_bill_detail_includes_receipt_branding(client, bill_environment):
    order = _new_unpaid_order(client, bill_environment)

    data = client.get(f"/api/bills/{order['id']}").json()["data"]

    cafe = data["cafe"]
    assert cafe["cafe_name"] == TEST_TAX_SETTINGS["cafe_name"]
    assert cafe["currency"] == "₹"
    assert cafe["receipt_footer"] == TEST_TAX_SETTINGS["receipt_footer"]
    assert {"cafe_name", "address", "phone", "logo_url", "currency", "receipt_footer"} <= set(cafe)

    bill = data["bill"]
    assert bill["order_number"].startswith("ORD-")
    assert len(bill["items"]) == 1
    assert {"subtotal", "discount_amount", "tax_percent", "tax_amount", "total"} <= set(bill)


def test_missing_bill_detail_returns_404(client):
    response = client.get("/api/bills/999999")

    assert response.status_code == 404
    assert response.json()["success"] is False
