import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.main import app
from app.models.employee import Employee
from app.models.salary import Salary

# Unique per-run tag so reruns never collide with leftover or hand-typed data.
RUN_TAG = uuid.uuid4().hex[:6]


def N(base: str) -> str:
    """Unique display name for this test run, e.g. 'Priya Sharma #3fa1b2'."""
    return f"{base} #{RUN_TAG}"


VALID_PAYLOAD = {
    "name": N("Priya Sharma"),
    "mobile": "9876543210",
    "email": "priya@cafe.in",
    "address": "21 Station Road, Pune",
    "role": "Chef",
    "joining_date": "2025-06-01",
    "salary_type": "Monthly",
    "base_salary": 25000,
    "is_active": True,
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def cleanup_tagged_employees():
    def purge():
        with SessionLocal() as db:
            tagged_ids = db.scalars(
                select(Employee.id).where(Employee.name.like(f"%#{RUN_TAG}"))
            ).all()
            if tagged_ids:
                db.execute(delete(Salary).where(Salary.employee_id.in_(tagged_ids)))
                db.execute(delete(Employee).where(Employee.id.in_(tagged_ids)))
                db.commit()

    purge()
    yield
    purge()


def _create(client, **overrides):
    payload = {**VALID_PAYLOAD, **overrides}
    return client.post("/api/employees", json=payload)


def test_create_employee_with_valid_data(client):
    response = _create(client)

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Employee created."
    data = body["data"]
    assert data["name"] == N("Priya Sharma")
    assert data["mobile"] == "9876543210"
    assert data["role"] == "Chef"
    assert data["salary_type"] == "Monthly"
    assert data["base_salary"] == 25000
    assert data["is_active"] is True
    assert data["salary_count"] == 0
    assert {"id", "joining_date", "created_at", "updated_at"}.issubset(data.keys())


def test_fields_are_trimmed_and_empty_become_null(client):
    response = _create(
        client,
        name=f"  {N('Spaced Name')}  ",
        email=None,
        address="   ",
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == N("Spaced Name")
    assert data["email"] is None
    assert data["address"] is None


def test_email_is_lowercased(client):
    created = _create(client, name=N("Case Co"), email=f"BIG{RUN_TAG}@Cafe.IN").json()["data"]
    assert created["email"] == f"big{RUN_TAG}@cafe.in"


def test_get_single_employee(client):
    created = _create(client, name=N("Fetch Me")).json()["data"]
    response = client.get(f"/api/employees/{created['id']}")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == N("Fetch Me")


def test_list_sorted_by_name(client):
    _create(client)
    _create(client, name=N("Amit Verma"))

    response = client.get("/api/employees")

    assert response.status_code == 200
    data = response.json()["data"]
    tagged = [item["name"] for item in data["items"] if item["name"].endswith(RUN_TAG)]
    assert len(tagged) >= 2
    assert tagged == sorted(tagged)


def test_search_matches_name_mobile_email_role(client):
    created = _create(
        client,
        name=N("Bean Barista"),
        mobile="9123456780",
        email=f"bean{RUN_TAG}@cafe.in",
        role="Waiter",
    ).json()["data"]

    by_name = client.get("/api/employees", params={"search": N("Bean Barista")}).json()
    assert created["id"] in [e["id"] for e in by_name["data"]["items"]]

    by_mobile = client.get("/api/employees", params={"search": "9123456780"}).json()
    assert created["id"] in [e["id"] for e in by_mobile["data"]["items"]]

    by_email = client.get("/api/employees", params={"search": f"bean{RUN_TAG}"}).json()
    assert created["id"] in [e["id"] for e in by_email["data"]["items"]]

    by_role_term = client.get("/api/employees", params={"search": "Waiter"}).json()
    assert created["id"] in [e["id"] for e in by_role_term["data"]["items"]]


def test_role_filter(client):
    chef = _create(client, name=N("Filter Chef"), role="Chef").json()["data"]
    manager = _create(client, name=N("Filter Manager"), role="Manager").json()["data"]

    chefs = client.get("/api/employees", params={"role": "Chef"}).json()
    ids = [e["id"] for e in chefs["data"]["items"]]
    assert chef["id"] in ids
    assert manager["id"] not in ids

    unknown = client.get("/api/employees", params={"role": "Wizard"})
    assert unknown.status_code == 422


def test_include_inactive_false_hides_rows(client):
    created = _create(client, name=N("Hidden Worker"), is_active=False).json()["data"]

    visible = client.get("/api/employees", params={"include_inactive": "false"}).json()
    assert created["id"] not in [e["id"] for e in visible["data"]["items"]]

    everything = client.get("/api/employees").json()
    assert created["id"] in [e["id"] for e in everything["data"]["items"]]


def test_update_employee(client):
    created = _create(client, name=N("Update Worker")).json()["data"]
    response = client.put(
        f"/api/employees/{created['id']}",
        json={
            "name": N("Update Worker Promoted"),
            "mobile": "9998887776",
            "email": "promoted@cafe.in",
            "address": None,
            "role": "Manager",
            "joining_date": "2025-06-01",
            "salary_type": "Monthly",
            "base_salary": 40000.5,
            "is_active": False,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == N("Update Worker Promoted")
    assert data["role"] == "Manager"
    assert data["base_salary"] == 40000.5
    assert data["is_active"] is False


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "   "},
        {"name": ""},
        {"name": None},
        {"name": "x" * 101},
        {"mobile": "12345"},
        {"mobile": "98765432109"},
        {"mobile": 9876543210},
        {"mobile": None},
        {"email": "not-an-email"},
        {"role": "Owner"},
        {"role": ""},
        {"salary_type": "Weekly"},
        {"salary_type": ""},
        {"base_salary": -1},
        {"base_salary": True},
        {"base_salary": "abc"},
        {"joining_date": "2099-01-01"},
        {"joining_date": "not-a-date"},
        {"joining_date": None},
        {"is_active": "yes-please"},
        {"address": "x" * 256},
    ],
    ids=[
        "blank-name",
        "empty-name",
        "missing-name",
        "name-too-long",
        "mobile-too-short",
        "mobile-too-long",
        "mobile-not-a-string",
        "missing-mobile",
        "email-invalid",
        "role-not-allowed",
        "role-empty",
        "salary-type-not-allowed",
        "salary-type-empty",
        "base-salary-negative",
        "base-salary-boolean",
        "base-salary-not-a-number",
        "joining-date-in-future",
        "joining-date-not-a-date",
        "missing-joining-date",
        "bad-flag-type",
        "address-too-long",
    ],
)
def test_create_with_invalid_data_fails_validation(client, changes):
    payload = {**VALID_PAYLOAD}
    for key, value in changes.items():
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value

    response = client.post("/api/employees", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert isinstance(body.get("errors"), list) and len(body["errors"]) > 0


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/api/employees/999999", None),
        ("put", "/api/employees/999999", {**VALID_PAYLOAD, "name": N("Ghost Worker")}),
        ("delete", "/api/employees/999999", None),
    ],
    ids=["get-missing", "put-missing", "delete-missing"],
)
def test_missing_employee_returns_404_envelope(client, method, path, body):
    response = getattr(client, method)(path, json=body) if body else getattr(client, method)(path)

    assert response.status_code == 404
    envelope = response.json()
    assert envelope["success"] is False
    assert "not found" in envelope["message"].lower()


def test_invalid_employee_id_in_path_is_422(client):
    response = client.get("/api/employees/not-a-number")

    assert response.status_code == 422


def test_delete_employee_then_404(client):
    created = _create(client, name=N("Temporary Worker")).json()["data"]
    response = client.delete(f"/api/employees/{created['id']}")

    assert response.status_code == 200
    assert response.json()["message"] == "Employee deleted."
    assert client.get(f"/api/employees/{created['id']}").status_code == 404
