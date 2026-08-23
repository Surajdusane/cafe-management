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


ITEM_KEYS = {
    "name",
    "description",
    "price",
    "image_url",
    "is_vegetarian",
    "is_popular",
    "is_available",
}
CATEGORY_KEYS = {"name", "description", "items"}
CAFE_KEYS = {"name", "address", "phone", "email", "logo_url", "currency"}

BRANDING_PAYLOAD = {
    "cafe_name": N("Public Brew Cafe"),
    "address": "7 MG Road, Pune",
    "phone": "9876543210",
    "email": f"menu{RUN_TAG}@brewbean.in",
    "logo_url": "/static/images/favicon.svg",
    "tax_percent": 5.0,
    "currency": "\u20B9",
    "receipt_footer": "See you soon!",
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def preserved_settings(client):
    """The branding test rewrites the global singleton; put the old values back."""
    original = client.get("/api/settings").json()["data"]
    yield original

    restore = {
        key: original[key]
        for key in [
            "cafe_name",
            "address",
            "phone",
            "email",
            "logo_url",
            "tax_percent",
            "currency",
            "receipt_footer",
        ]
    }
    client.put("/api/settings", json=restore)


@pytest.fixture(scope="module", autouse=True)
def menu_fixture_data(client):
    """Two live sections, one inactive section and one empty section."""
    live_a = client.post("/api/categories", json={"name": N("Hot Drinks")}).json()["data"]
    live_b = client.post("/api/categories", json={"name": N("Snacks")}).json()["data"]
    inactive = client.post(
        "/api/categories", json={"name": N("Hidden Section"), "is_active": False}
    ).json()["data"]
    empty = client.post("/api/categories", json={"name": N("Empty Section")}).json()["data"]

    def make(category_id, name, **overrides):
        payload = {"category_id": category_id, "name": name, "price": 50, **overrides}
        response = client.post("/api/menu/items", json=payload)
        assert response.status_code == 201, response.text
        return response.json()["data"]

    make(live_a["id"], N("Filter Coffee"), price=60, description="South Indian style", is_popular=True)
    make(
        live_a["id"],
        N("Chocolate Cake"),
        price=110,
        is_available=False,
        is_vegetarian=False,
    )
    make(live_b["id"], N("Veg Sandwich"), price=80)

    yield {}

    with SessionLocal() as db:
        tagged_categories = db.scalars(
            select(Category.id).where(Category.name.like(f"%#{RUN_TAG}"))
        ).all()
        if tagged_categories:
            db.execute(delete(MenuItem).where(MenuItem.category_id.in_(tagged_categories)))
            db.execute(delete(Category).where(Category.id.in_(tagged_categories)))
            db.commit()


def test_public_menu_page_serves_html_without_admin_shell(client):
    response = client.get("/menu/cafe")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    # The customer page loads its own assets and never the admin shell/navigation.
    assert "/static/js/public-menu.js" in html
    assert "/static/css/public-menu.css" in html
    assert 'data-page=' not in html
    assert "/static/js/common.js" not in html


def test_public_endpoint_returns_envelope(client):
    response = client.get("/api/public/menu")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert set(body["data"].keys()) == {"cafe", "categories"}


def test_branding_comes_from_settings(client):
    client.put("/api/settings", json=BRANDING_PAYLOAD)
    cafe = client.get("/api/public/menu").json()["data"]["cafe"]

    assert cafe["name"] == BRANDING_PAYLOAD["cafe_name"]
    assert cafe["address"] == BRANDING_PAYLOAD["address"]
    assert cafe["phone"] == BRANDING_PAYLOAD["phone"]
    assert cafe["email"] == BRANDING_PAYLOAD["email"]
    assert cafe["logo_url"] == BRANDING_PAYLOAD["logo_url"]
    assert cafe["currency"] == BRANDING_PAYLOAD["currency"]


def test_only_active_non_empty_sections_are_listed(client):
    data = client.get("/api/public/menu").json()["data"]
    section_names = [category["name"] for category in data["categories"]]

    assert N("Hot Drinks") in section_names
    assert N("Snacks") in section_names
    assert N("Hidden Section") not in section_names  # inactive
    assert N("Empty Section") not in section_names  # no items


def test_sold_out_items_remain_visible_but_flagged(client):
    data = client.get("/api/public/menu").json()["data"]
    hot_drinks = next(c for c in data["categories"] if c["name"] == N("Hot Drinks"))
    cake = next(i for i in hot_drinks["items"] if i["name"] == N("Chocolate Cake"))

    assert cake["is_available"] is False
    assert cake["price"] == 110.0


def test_item_flags_pass_through_to_customers(client):
    data = client.get("/api/public/menu").json()["data"]
    hot_drinks = next(c for c in data["categories"] if c["name"] == N("Hot Drinks"))
    coffee = next(i for i in hot_drinks["items"] if i["name"] == N("Filter Coffee"))

    assert coffee["is_available"] is True
    assert coffee["is_popular"] is True
    assert coffee["is_vegetarian"] is True
    assert coffee["description"] == "South Indian style"


def test_response_contains_no_internal_fields(client):
    data = client.get("/api/public/menu").json()["data"]

    assert set(data["cafe"].keys()) == CAFE_KEYS
    for category in data["categories"]:
        assert set(category.keys()) == CATEGORY_KEYS
        for item in category["items"]:
            assert set(item.keys()) == ITEM_KEYS


def test_sections_and_items_are_sorted_alphabetically(client):
    data = client.get("/api/public/menu").json()["data"]

    section_names = [c["name"] for c in data["categories"]]
    assert section_names == sorted(section_names, key=str.lower)

    for category in data["categories"]:
        item_names = [i["name"] for i in category["items"]]
        assert item_names == sorted(item_names, key=str.lower)


def test_admin_share_page_and_public_page_coexist(client):
    assert client.get("/customer-menu").status_code == 200
    assert client.get("/menu/cafe").status_code == 200
