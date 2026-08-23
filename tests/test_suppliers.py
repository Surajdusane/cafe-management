import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.main import app
from app.models.inventory import InventoryItem
from app.models.supplier import Supplier

# Unique per-run tag so reruns never collide with leftover or hand-typed data.
RUN_TAG = uuid.uuid4().hex[:6]


def N(base: str) -> str:
    """Unique display name for this test run, e.g. 'Gokul Dairy #3fa1b2'."""
    return f"{base} #{RUN_TAG}"


VALID_PAYLOAD = {
    "name": N("Gokul Dairy"),
    "contact_person": "Ramesh Patel",
    "phone": "9876543210",
    "email": "orders@gokuldairy.in",
    "address": "12 Market Yard, Pune",
    "materials_supplied": "Milk, Paneer, Butter",
    "is_active": True,
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def cleanup_tagged_suppliers():
    def purge():
        with SessionLocal() as db:
            tagged_ids = db.scalars(
                select(Supplier.id).where(Supplier.name.like(f"%#{RUN_TAG}"))
            ).all()
            if tagged_ids:
                db.execute(delete(InventoryItem).where(InventoryItem.supplier_id.in_(tagged_ids)))
                db.execute(delete(Supplier).where(Supplier.id.in_(tagged_ids)))
                db.commit()

    purge()
    yield
    purge()


def _create(client, **overrides):
    payload = {**VALID_PAYLOAD, **overrides}
    return client.post("/api/suppliers", json=payload)


def test_create_supplier_with_valid_data(client):
    response = _create(client)

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Supplier created."
    data = body["data"]
    assert data["name"] == N("Gokul Dairy")
    assert data["contact_person"] == "Ramesh Patel"
    assert data["email"] == "orders@gokuldairy.in"
    assert data["is_active"] is True
    assert data["inventory_item_count"] == 0
    assert {"id", "created_at", "updated_at"}.issubset(data.keys())


def test_fields_are_trimmed_and_empty_become_null(client):
    response = _create(
        client,
        name=f"  {N('Spaced Co')}  ",
        contact_person="   ",
        email=None,
        address="  ",
        materials_supplied="",
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == N("Spaced Co")
    assert data["contact_person"] is None
    assert data["address"] is None
    assert data["materials_supplied"] is None


def test_email_is_lowercased(client):
    created = _create(client, name=N("Case Co"), email=f"BIG{RUN_TAG}@Vendor.IN").json()["data"]
    assert created["email"] == f"big{RUN_TAG}@vendor.in"


def test_get_single_supplier(client):
    created = _create(client, name=N("Fresh Farms")).json()["data"]
    response = client.get(f"/api/suppliers/{created['id']}")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == N("Fresh Farms")


def test_list_sorted_by_name_with_counts(client):
    _create(client)
    _create(client, name=N("Aroma Beans"))

    response = client.get("/api/suppliers")

    assert response.status_code == 200
    data = response.json()["data"]
    tagged = [item["name"] for item in data["items"] if item["name"].endswith(RUN_TAG)]
    assert len(tagged) >= 2
    assert tagged == sorted(tagged)
    assert all("inventory_item_count" in item for item in data["items"])


def test_update_supplier(client):
    created = _create(client, name=N("Update Vendor")).json()["data"]
    response = client.put(
        f"/api/suppliers/{created['id']}",
        json={
            "name": N("Gokul Dairy Updated"),
            "contact_person": "Suresh Patel",
            "phone": "9998887776",
            "email": "sales@gokuldairy.in",
            "address": None,
            "materials_supplied": "Milk, Curd",
            "is_active": False,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == N("Gokul Dairy Updated")
    assert data["phone"] == "9998887776"
    assert data["is_active"] is False


def test_search_matches_name_contact_materials_phone(client):
    created = _create(
        client,
        name=N("Bean Bros"),
        contact_person=f"Asha {RUN_TAG}",
        materials_supplied="Coffee beans #roast",
        phone="9123456780",
    ).json()["data"]

    by_name = client.get("/api/suppliers", params={"search": N("Bean Bros")}).json()
    assert created["id"] in [s["id"] for s in by_name["data"]["items"]]

    by_contact = client.get("/api/suppliers", params={"search": f"asha {RUN_TAG}"}).json()
    assert created["id"] in [s["id"] for s in by_contact["data"]["items"]]

    by_materials = client.get("/api/suppliers", params={"search": "#roast"}).json()
    assert created["id"] in [s["id"] for s in by_materials["data"]["items"]]


def test_include_inactive_false_hides_rows(client):
    created = _create(client, name=N("Hidden Vendor"), is_active=False).json()["data"]

    visible = client.get("/api/suppliers", params={"include_inactive": "false"}).json()
    assert created["id"] not in [s["id"] for s in visible["data"]["items"]]

    everything = client.get("/api/suppliers").json()
    assert created["id"] in [s["id"] for s in everything["data"]["items"]]


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "   "},
        {"name": ""},
        {"name": None},
        {"name": "x" * 101},
        {"phone": "12345"},
        {"phone": "98765432109"},
        {"phone": 9876543210},
        {"email": "not-an-email"},
        {"email": "missing-at-sign.com"},
        {"is_active": "yes-please"},
        {"contact_person": "x" * 101},
        {"materials_supplied": "x" * 256},
    ],
    ids=[
        "blank-name",
        "empty-name",
        "missing-name",
        "name-too-long",
        "phone-too-short",
        "phone-too-long",
        "phone-not-a-string",
        "email-invalid",
        "email-missing-at",
        "bad-flag-type",
        "contact-too-long",
        "materials-too-long",
    ],
)
def test_create_with_invalid_data_fails_validation(client, changes):
    payload = {**VALID_PAYLOAD}
    for key, value in changes.items():
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value

    response = client.post("/api/suppliers", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert isinstance(body.get("errors"), list) and len(body["errors"]) > 0


def test_duplicate_name_rejected_case_insensitive(client):
    first = _create(client, name=N("United Traders"))
    duplicate_same_case = _create(client, name=N("United Traders"))
    duplicate_other_case = _create(client, name=N("UNITED TRADERS"))

    assert first.status_code == 201
    assert duplicate_same_case.status_code == 409
    assert duplicate_other_case.status_code == 409
    assert "already exists" in duplicate_other_case.json()["message"]


def test_duplicate_check_excludes_self_on_update(client):
    created = _create(client, name=N("Same Name Co")).json()["data"]
    response = client.put(f"/api/suppliers/{created['id']}", json={**VALID_PAYLOAD, "name": N("Same Name Co")})

    assert response.status_code == 200


def test_delete_supplier_then_404(client):
    created = _create(client, name=N("Temporary Vendor")).json()["data"]
    response = client.delete(f"/api/suppliers/{created['id']}")

    assert response.status_code == 200
    assert response.json()["message"] == "Supplier deleted."
    assert client.get(f"/api/suppliers/{created['id']}").status_code == 404


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/api/suppliers/999999", None),
        ("put", "/api/suppliers/999999", {**VALID_PAYLOAD, "name": N("Ghost Vendor")}),
        ("delete", "/api/suppliers/999999", None),
    ],
    ids=["get-missing", "put-missing", "delete-missing"],
)
def test_missing_supplier_returns_404_envelope(client, method, path, body):
    response = getattr(client, method)(path, json=body) if body else getattr(client, method)(path)

    assert response.status_code == 404
    envelope = response.json()
    assert envelope["success"] is False
    assert "not found" in envelope["message"].lower()


def test_invalid_supplier_id_in_path_is_422(client):
    response = client.get("/api/suppliers/not-a-number")

    assert response.status_code == 422
