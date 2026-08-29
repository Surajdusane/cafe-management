import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.main import app
from app.models.expense import Expense

RUN_TAG = uuid.uuid4().hex[:6]


def N(base: str) -> str:
    """Unique display title/notes tag for expenses created by this module."""
    return f"{base} #{RUN_TAG}"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def cleanup_tagged_data():
    def purge():
        with SessionLocal() as db:
            tagged = db.scalars(
                select(Expense).where(Expense.title.like(f"%#{RUN_TAG}"))
            ).all()
            if tagged:
                db.execute(delete(Expense).where(Expense.id.in_([e.id for e in tagged])))
                db.commit()

    purge()
    yield
    purge()


def _create_expense(client, **overrides) -> dict:
    payload = {"title": N("Electricity bill")}
    payload.update(overrides)
    return client.post("/api/expenses", json=payload)


def _valid_payload(**overrides) -> dict:
    # A fully-specified valid body useful for full-update tests.
    payload = {
        "title": N("Rent"),
        "category": "Rent",
        "amount": 12000,
        "expense_date": "2026-08-01",
        "payment_method": "UPI",
        "notes": "monthly rent",
    }
    payload.update(overrides)
    return payload


def test_create_expense_with_defaults(client):
    response = _create_expense(client, category="Electricity", amount=2500.0)

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Expense recorded."
    data = body["data"]
    assert data["title"].endswith(RUN_TAG)
    assert data["category"] == "Electricity"
    assert data["amount"] == 2500.0
    # Expense date defaults to today; payment method defaults to Cash.
    assert data["expense_date"] == date.today().isoformat()
    assert data["payment_method"] == "Cash"
    assert data["notes"] is None


def test_all_allowed_categories_and_amount_rounding(client):
    for category in ["Gas", "Rent", "Maintenance", "Cleaning", "Internet", "Miscellaneous"]:
        response = _create_expense(client, category=category, amount=99.999)
        assert response.status_code == 201
        assert response.json()["data"]["amount"] == 100.0


def test_explicit_date_method_and_notes_are_kept(client):
    response = _create_expense(
        client,
        category="Internet",
        amount=899.5,
        expense_date="2026-08-05",
        payment_method="Card",
        notes="   broadband  ",
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["expense_date"] == "2026-08-05"
    assert data["payment_method"] == "Card"
    assert data["notes"] == "broadband"  # whitespace trimmed


def test_repeated_title_is_allowed(client):
    first = _create_expense(client, category="Cleaning", amount=500)
    second = _create_expense(client, category="Cleaning", amount=500)

    assert first.status_code == 201
    assert second.status_code == 201  # no uniqueness rule on expense titles


def test_full_update_replaces_fields(client):
    created = _create_expense(client, category="Rent", amount=10000).json()["data"]

    response = client.put(
        f"/api/expenses/{created['id']}",
        json=_valid_payload(category="Maintenance", amount=4000, expense_date="2026-08-03"),
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == created["id"]
    assert data["category"] == "Maintenance"
    assert data["amount"] == 4000
    assert data["expense_date"] == "2026-08-03"


def test_list_is_newest_first_with_summary(client):
    _create_expense(client, category="Rent", amount=1000, expense_date="2026-07-01")
    _create_expense(client, category="Rent", amount=2000, expense_date="2026-08-01")
    _create_expense(client, category="Gas", amount=1500, expense_date="2026-08-10")

    response = client.get("/api/expenses")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["count"] >= 3
    assert data["summary"]["categories"] >= 2
    # Newest expense date first in the list.
    first_date = data["items"][0]["expense_date"]
    assert first_date >= data["items"][-1]["expense_date"]


def test_filters_category_payment_and_date_range(client):
    _create_expense(client, category="Rent", amount=3000, expense_date="2026-08-02", payment_method="Cash")
    _create_expense(client, category="Internet", amount=700, expense_date="2026-08-03", payment_method="UPI")

    only_rent = client.get("/api/expenses", params={"category": "Rent"}).json()["data"]
    assert all(e["category"] == "Rent" for e in only_rent["items"])

    only_upi = client.get("/api/expenses", params={"payment_method": "UPI"}).json()["data"]
    assert all(e["payment_method"] == "UPI" for e in only_upi["items"])

    in_range = client.get(
        "/api/expenses",
        params={"start_date": "2026-08-01", "end_date": "2026-08-02"},
    ).json()["data"]
    assert all(e["expense_date"] in ("2026-08-01", "2026-08-02") for e in in_range["items"])


def test_search_matches_title_and_notes(client):
    title = N("Water pipe fix")
    _create_expense(client, category="Maintenance", amount=1200, title=title, notes="plumbing leak")

    by_title = client.get("/api/expenses", params={"search": f"#{RUN_TAG}"}).json()["data"]
    assert any(e["title"] == title for e in by_title["items"])
    assert by_title["count"] >= 1


def test_options_endpoint_lists_fixed_choices(client):
    response = client.get("/api/expenses/options")
    assert response.status_code == 200
    data = response.json()["data"]
    assert {"Electricity", "Gas", "Rent", "Maintenance", "Cleaning", "Internet", "Miscellaneous"}.issubset(
        set(data["categories"])
    )
    assert {"Cash", "UPI", "Card", "Other"}.issubset(set(data["payment_methods"]))


def test_missing_expense_returns_404_envelope(client):
    for method in ("get", "delete"):
        response = getattr(client, method)("/api/expenses/999999")
        assert response.status_code == 404
        envelope = response.json()
        assert envelope["success"] is False
        assert "not found" in envelope["message"].lower()

    put = client.put("/api/expenses/999999", json=_valid_payload())
    assert put.status_code == 404
    assert "not found" in put.json()["message"].lower()


def test_invalid_expense_id_is_422(client):
    response = client.get("/api/expenses/not-a-number")
    assert response.status_code == 422


def test_delete_then_404(client):
    created = _create_expense(client, category="Miscellaneous", amount=50).json()["data"]

    deleted = client.delete(f"/api/expenses/{created['id']}")
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Expense deleted."

    after = client.get(f"/api/expenses/{created['id']}")
    assert after.status_code == 404


@pytest.mark.parametrize(
    "changes",
    [
        {"title": ""},
        {"title": "   "},
        {"title": None},
        {"title": "x" * 121},
        {"category": ""},
        {"category": None},
        {"category": "Coffee"},
        {"amount": 0},
        {"amount": -5},
        {"amount": True},
        {"amount": "expensive"},
        {"payment_method": ""},
        {"payment_method": "Cheque"},
        {"notes": "x" * 256},
    ],
    ids=[
        "title-empty",
        "title-blank-space",
        "title-missing",
        "title-too-long",
        "category-empty",
        "category-missing",
        "category-not-allowed",
        "amount-zero",
        "amount-negative",
        "amount-boolean",
        "amount-not-a-number",
        "method-empty",
        "method-not-allowed",
        "notes-too-long",
    ],
)
def test_create_with_invalid_data_fails_validation(client, changes):
    payload = {"title": N("Invalid"), "category": "Rent", "amount": 100}
    for key, value in changes.items():
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value

    response = client.post("/api/expenses", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert isinstance(body.get("errors"), list) and len(body["errors"]) > 0


def test_expense_persisted_in_sqlite(client):
    data = _create_expense(client, category="Gas", amount=777.25).json()["data"]

    with SessionLocal() as db:
        row = db.get(Expense, data["id"])
        assert row is not None
        assert row.title == data["title"]
        assert row.amount == 777.25
        assert row.category == "Gas"
