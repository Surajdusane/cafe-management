import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.main import app
from app.models.category import Category
from app.models.menu_item import MenuItem

# Tagged names keep this module isolated from real data and previous runs.
RUN_TAG = uuid.uuid4().hex[:6]


def N(base: str) -> str:
    return f"{base} #{RUN_TAG}"


CATEGORY_NAME = N("QA Category")
VALID_PAYLOAD = {
    "category_id": None,  # filled in by managed_category
    "name": N("Cappuccino"),
    "description": "Espresso with steamed milk",
    "price": 120.0,
    "image_url": "/static/images/favicon.svg",
    "is_vegetarian": True,
    "is_popular": False,
    "is_available": True,
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def managed_category(client):
    """One category for the whole module; removed again with all its items."""
    response = client.post("/api/categories", json={"name": CATEGORY_NAME})
    assert response.status_code == 201, response.text
    category_id = response.json()["data"]["id"]

    VALID_PAYLOAD["category_id"] = category_id

    yield {"id": category_id}

    with SessionLocal() as db:
        tagged_categories = db.scalars(
            select(Category.id).where(Category.name.like(f"%#{RUN_TAG}"))
        ).all()
        if tagged_categories:
            db.execute(delete(MenuItem).where(MenuItem.category_id.in_(tagged_categories)))
            db.execute(delete(Category).where(Category.id.in_(tagged_categories)))
            db.commit()


@pytest.fixture()
def second_category(client):
    """A short-lived extra category for cross-category tests."""
    response = client.post("/api/categories", json={"name": N("Second Category")})
    assert response.status_code == 201
    data = response.json()["data"]

    yield data

    with SessionLocal() as db:
        category = db.get(Category, data["id"])
        if category is not None:
            db.delete(category)  # items cascade
            db.commit()


def _create(client, **overrides):
    payload = {**VALID_PAYLOAD, **overrides}
    return client.post("/api/menu/items", json=payload)


def test_create_item_with_valid_data(client):
    response = _create(client)

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Menu item created."
    data = body["data"]
    assert data["name"] == N("Cappuccino")
    assert data["price"] == 120.0
    assert data["is_available"] is True
    assert data["is_popular"] is False
    assert data["category"]["id"] == VALID_PAYLOAD["category_id"]
    assert data["category"]["name"] == CATEGORY_NAME


def test_create_uses_sane_defaults(client):
    minimal = client.post(
        "/api/menu/items",
        json={"category_id": VALID_PAYLOAD["category_id"], "name": N("Plain Tea"), "price": 20},
    )

    assert minimal.status_code == 201
    data = minimal.json()["data"]
    assert data["is_vegetarian"] is True
    assert data["is_popular"] is False
    assert data["is_available"] is True
    assert data["description"] is None


def test_price_is_rounded_to_two_decimals(client):
    created = _create(client, name=N("Rounded Latte"), price=99.999).json()["data"]

    assert created["price"] == 100.0


def test_get_single_item(client):
    created = _create(client, name=N("Mocha")).json()["data"]
    response = client.get(f"/api/menu/items/{created['id']}")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == N("Mocha")


def test_update_item_full_replace(client):
    created = _create(client, name=N("Hot Chocolate")).json()["data"]
    payload = {
        **VALID_PAYLOAD,
        "name": N("Belgian Hot Chocolate"),
        "price": 150.5,
        "is_popular": True,
        "is_available": False,
    }
    response = client.put(f"/api/menu/items/{created['id']}", json=payload)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == N("Belgian Hot Chocolate")
    assert data["price"] == 150.5
    assert data["is_popular"] is True
    assert data["is_available"] is False


def test_move_item_to_another_category(client, second_category):
    created = _create(client, name=N("Cross Cat Item")).json()["data"]
    payload = {**VALID_PAYLOAD, "name": N("Cross Cat Item"), "category_id": second_category["id"]}
    response = client.put(f"/api/menu/items/{created['id']}", json=payload)

    assert response.status_code == 200
    moved = response.json()["data"]
    assert moved["category_id"] == second_category["id"]
    assert moved["category"]["name"] == N("Second Category")


def test_same_name_allowed_in_different_categories(client, second_category):
    first = _create(client, name=N("Shared Name"))
    second = _create(client, name=N("Shared Name"), category_id=second_category["id"])

    assert first.status_code == 201
    assert second.status_code == 201


def test_search_filter_matches_name_and_description(client):
    _create(client, name=N("Veg Sandwich"), description="Grilled sandwich")

    by_name = client.get("/api/menu/items", params={"search": N("Sandwich")}).json()
    assert N("Veg Sandwich") in [item["name"] for item in by_name["data"]["items"]]

    by_description = client.get("/api/menu/items", params={"search": "Grilled"}).json()
    assert N("Veg Sandwich") in [item["name"] for item in by_description["data"]["items"]]


def test_category_filter_returns_only_that_category(client, second_category):
    mine = _create(client, name=N("Filter Target")).json()["data"]
    _create(client, name=N("Other Cat Item"), category_id=second_category["id"])

    response = client.get("/api/menu/items", params={"category_id": mine["category_id"]}).json()

    items = response["data"]["items"]
    assert items
    assert all(item["category_id"] == mine["category_id"] for item in items)


def test_availability_filter_excludes_sold_out_items(client):
    _create(client, name=N("Sold Out Cake"), is_available=False)
    available_only = client.get("/api/menu/items", params={"available_only": "true"}).json()

    assert available_only["success"] is True
    assert all(item["is_available"] for item in available_only["data"]["items"])


@pytest.mark.parametrize(
    "payload",
    [
        {k: v for k, v in VALID_PAYLOAD.items() if k != "category_id"},
        {**VALID_PAYLOAD, "category_id": 0},
        {**VALID_PAYLOAD, "category_id": -3},
        {**VALID_PAYLOAD, "category_id": "abc"},
        {**VALID_PAYLOAD, "name": ""},
        {k: v for k, v in VALID_PAYLOAD.items() if k != "name"},
        {**VALID_PAYLOAD, "name": "x" * 121},
        {**VALID_PAYLOAD, "price": 0},
        {**VALID_PAYLOAD, "price": -50},
        {**VALID_PAYLOAD, "price": "expensive"},
        {**VALID_PAYLOAD, "description": "x" * 501},
        {**VALID_PAYLOAD, "image_url": "x" * 301},
    ],
    ids=[
        "missing-category",
        "zero-category-id",
        "negative-category-id",
        "non-numeric-category-id",
        "blank-name",
        "missing-name",
        "name-too-long",
        "zero-price",
        "negative-price",
        "non-numeric-price",
        "description-too-long",
        "image-url-too-long",
    ],
)
def test_create_with_invalid_data_fails_validation(client, payload):
    response = client.post("/api/menu/items", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert isinstance(body.get("errors"), list) and len(body["errors"]) > 0


def test_unknown_category_returns_404_message(client):
    response = client.post("/api/menu/items", json={**VALID_PAYLOAD, "category_id": 999999})

    assert response.status_code == 404
    assert "not found" in response.json()["message"].lower()


def test_duplicate_name_in_same_category_rejected_case_insensitive(client):
    first = _create(client, name=N("Signature Cold Coffee"))
    duplicate_exact = _create(client, name=N("Signature Cold Coffee"))
    duplicate_case = _create(client, name=N("SIGNATURE COLD COFFEE"))

    assert first.status_code == 201
    assert duplicate_exact.status_code == 409
    assert duplicate_case.status_code == 409
    assert "already exists" in duplicate_case.json()["message"]


def test_duplicate_check_excludes_self_on_update(client):
    created = _create(client, name=N("Blueberry Muffin")).json()["data"]
    response = client.put(
        f"/api/menu/items/{created['id']}",
        json={**VALID_PAYLOAD, "name": N("Blueberry Muffin"), "price": 80},
    )

    assert response.status_code == 200


def test_delete_item_then_missing(client):
    created = _create(client, name=N("Disposable Cookie")).json()["data"]
    deleted = client.delete(f"/api/menu/items/{created['id']}")

    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Menu item deleted."
    assert client.get(f"/api/menu/items/{created['id']}").status_code == 404


def test_failed_duplicate_create_leaves_table_untouched(client):
    before = client.get("/api/menu/items").json()["data"]["count"]
    client.post("/api/menu/items", json=VALID_PAYLOAD)  # duplicate of first Cappuccino -> 409
    after = client.get("/api/menu/items").json()["data"]["count"]

    assert before == after


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/api/menu/items/999999", None),
        ("put", "/api/menu/items/999999", VALID_PAYLOAD),
        ("delete", "/api/menu/items/999999", None),
    ],
    ids=["get-missing", "put-missing", "delete-missing"],
)
def test_missing_item_returns_404_envelope(client, method, path, body):
    response = getattr(client, method)(path, json=body) if body else getattr(client, method)(path)

    assert response.status_code == 404
    envelope = response.json()
    assert envelope["success"] is False
    assert "not found" in envelope["message"].lower()


def test_items_persist_in_database(client):
    created = _create(client, name=N("Persistence Brownie")).json()["data"]

    with SessionLocal() as db:
        row = db.get(MenuItem, created["id"])
        assert row is not None
        assert row.name == N("Persistence Brownie")
        assert row.price == pytest.approx(120.0)


def test_no_orphan_rows_left_behind(client):
    """Every menu item in this database belongs to an existing category."""
    with SessionLocal() as db:
        orphaned = db.scalars(
            select(MenuItem).where(~MenuItem.category_id.in_(select(Category.id)))
        ).all()

    assert orphaned == []
