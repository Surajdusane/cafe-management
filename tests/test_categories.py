import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.main import app
from app.models.category import Category
from app.models.menu_item import MenuItem

# Every row created by this module carries the run tag in its name, so reruns
# can never collide with data left behind by an earlier run or typed in by hand.
RUN_TAG = uuid.uuid4().hex[:6]


def N(base: str) -> str:
    """Unique display name for this test run, e.g. 'Coffee #3fa1b2'."""
    return f"{base} #{RUN_TAG}"


VALID_PAYLOAD = {
    "name": N("Coffee"),
    "description": "Espresso-based hot drinks",
    "is_active": True,
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def cleanup_tagged_categories():
    """Remove tagged rows left by previous crashed runs, then clean up again."""
    def purge():
        with SessionLocal() as db:
            tagged_ids = db.scalars(
                select(Category.id).where(Category.name.like(f"%#{RUN_TAG}"))
            ).all()
            if tagged_ids:
                db.execute(delete(MenuItem).where(MenuItem.category_id.in_(tagged_ids)))
                db.execute(delete(Category).where(Category.id.in_(tagged_ids)))
                db.commit()

    purge()
    yield
    purge()


def _create(client, **overrides):
    payload = {**VALID_PAYLOAD, **overrides}
    return client.post("/api/categories", json=payload)


def test_create_category_with_valid_data(client):
    response = _create(client)

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Category created."
    data = body["data"]
    assert data["name"] == N("Coffee")
    assert data["description"] == "Espresso-based hot drinks"
    assert data["is_active"] is True
    assert data["item_count"] == 0
    assert {"id", "created_at", "updated_at"}.issubset(data.keys())


def test_name_is_trimmed_on_create(client):
    response = _create(client, name=f"   {N('Snacks')}   ")

    assert response.status_code == 201
    assert response.json()["data"]["name"] == N("Snacks")


def test_empty_description_becomes_null(client):
    response = _create(client, name=N("Tea"), description="   ")

    assert response.status_code == 201
    assert response.json()["data"]["description"] is None


def test_get_single_category(client):
    created = _create(client, name=N("Beverages")).json()["data"]
    response = client.get(f"/api/categories/{created['id']}")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == N("Beverages")


def test_list_categories_returns_created_rows_sorted_by_name(client):
    _create(client)
    _create(client, name=N("Snacks"))

    response = client.get("/api/categories")

    assert response.status_code == 200
    data = response.json()["data"]
    tagged_names = [item["name"] for item in data["items"] if item["name"].endswith(RUN_TAG)]
    assert len(tagged_names) >= 2
    assert tagged_names == sorted(tagged_names)
    assert data["count"] == len(data["items"])
    assert all("item_count" in item for item in data["items"])


def test_update_category_with_valid_data(client):
    created = _create(client, name=N("Desserts")).json()["data"]
    response = client.put(
        f"/api/categories/{created['id']}",
        json={"name": N("Sweet Desserts"), "description": "Cakes and pastries", "is_active": False},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == N("Sweet Desserts")
    assert data["is_active"] is False
    assert data["item_count"] == 0


def test_search_filter_matches_name_and_description(client):
    _create(client, name=N("Breads"), description="Fresh bakery bakes")

    by_description = client.get("/api/categories", params={"search": "bakery"}).json()
    assert N("Breads") in [item["name"] for item in by_description["data"]["items"]]

    by_name = client.get("/api/categories", params={"search": N("Breads")}).json()
    assert N("Breads") in [item["name"] for item in by_name["data"]["items"]]


def test_include_inactive_false_hides_inactive_rows(client):
    created = _create(client, name=N("Hidden Cat"), is_active=False).json()["data"]

    visible = client.get("/api/categories", params={"include_inactive": "false"}).json()
    visible_names = [item["name"] for item in visible["data"]["items"]]
    assert created["name"] not in visible_names

    everything = client.get("/api/categories").json()["data"]
    assert created["name"] in [item["name"] for item in everything["items"]]


@pytest.mark.parametrize(
    "payload",
    [
        {**VALID_PAYLOAD, "name": "   "},
        {k: v for k, v in VALID_PAYLOAD.items() if k != "name"},
        {**VALID_PAYLOAD, "name": "x" * 81},
        {**VALID_PAYLOAD, "description": "x" * 256},
        {**VALID_PAYLOAD, "is_active": "yes-please"},
    ],
    ids=["blank-name", "missing-name", "name-too-long", "description-too-long", "bad-flag-type"],
)
def test_create_with_invalid_data_fails_validation(client, payload):
    response = client.post("/api/categories", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert isinstance(body.get("errors"), list) and len(body["errors"]) > 0


def test_duplicate_name_rejected_case_insensitive(client):
    first = _create(client, name=N("Juices"))
    duplicate_same_case = _create(client, name=N("Juices"))
    duplicate_other_case = _create(client, name=N("JUICES"))

    assert first.status_code == 201
    assert duplicate_same_case.status_code == 409
    assert duplicate_other_case.status_code == 409
    assert "already exists" in duplicate_other_case.json()["message"]


def test_duplicate_check_excludes_self_on_update(client):
    created = _create(client, name=N("Shakes")).json()["data"]
    response = client.put(
        f"/api/categories/{created['id']}",
        json={"name": N("Shakes"), "description": "Thick shakes", "is_active": True},
    )

    assert response.status_code == 200


def test_failed_create_leaves_table_untouched(client):
    before = client.get("/api/categories").json()["data"]["count"]
    client.post("/api/categories", json=VALID_PAYLOAD)  # duplicate -> 409
    after = client.get("/api/categories").json()["data"]["count"]

    assert before == after


def test_delete_category_without_items(client):
    created = _create(client, name=N("Temporary")).json()["data"]
    response = client.delete(f"/api/categories/{created['id']}")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert client.get(f"/api/categories/{created['id']}").status_code == 404


def test_recreate_after_delete_succeeds(client):
    created = _create(client, name=N("Recyclable")).json()["data"]
    client.delete(f"/api/categories/{created['id']}")
    again = _create(client, name=N("Recyclable"))

    assert again.status_code == 201


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/api/categories/999999", None),
        ("put", "/api/categories/999999", {**VALID_PAYLOAD, "name": N("Ghost")}),
        ("delete", "/api/categories/999999", None),
    ],
    ids=["get-missing", "put-missing", "delete-missing"],
)
def test_missing_category_returns_404_envelope(client, method, path, body):
    response = getattr(client, method)(path, json=body) if body else getattr(client, method)(path)

    assert response.status_code == 404
    envelope = response.json()
    assert envelope["success"] is False
    assert "not found" in envelope["message"].lower()


def test_invalid_category_id_in_path_is_422(client):
    response = client.get("/api/categories/not-a-number")

    assert response.status_code == 422
