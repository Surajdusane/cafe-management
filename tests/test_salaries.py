from datetime import date
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
    """Unique display name for employees created by this module."""
    return f"{base} #{RUN_TAG}"


def _employee_payload(name: str, base_salary: float = 20000, role: str = "Waiter") -> dict:
    return {
        "name": N(name),
        "mobile": "9876543210",
        "email": None,
        "address": None,
        "role": role,
        "joining_date": "2025-01-10",
        "salary_type": "Monthly",
        "base_salary": base_salary,
        "is_active": True,
    }


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def cleanup_tagged_data():
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


def _create_employee(client, **overrides) -> dict:
    name = overrides.pop("name", "Ravi Kumar")
    payload = {**_employee_payload(name), **overrides}
    response = client.post("/api/employees", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _create_salary(client, employee_id: int, month: str, **overrides):
    payload = {"employee_id": employee_id, "salary_month": month, **overrides}
    return client.post("/api/salaries", json=payload)


def test_create_salary_with_explicit_base_calculates_net(client):
    employee = _create_employee(client, name="Calc Worker", base_salary=25000)
    response = _create_salary(
        client, employee["id"], "2026-07", base_salary=25000, bonus=1500, deduction=300
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Salary record created."
    data = body["data"]
    # Net Salary = Base + Bonus - Deduction (calculated on the server).
    assert data["net_salary"] == 26200.0
    assert data["base_salary"] == 25000
    assert data["bonus"] == 1500
    assert data["deduction"] == 300
    assert data["payment_status"] == "Unpaid"
    assert data["employee"]["id"] == employee["id"]
    assert data["employee"]["name"].endswith(RUN_TAG)


def test_missing_base_salary_copies_employee_base(client):
    employee = _create_employee(client, name="Fallback Worker", base_salary=18000)
    response = _create_salary(client, employee["id"], "2026-07", bonus=500)

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["base_salary"] == 18000
    assert data["net_salary"] == 18500.0


def test_amounts_are_rounded_to_two_decimals(client):
    employee = _create_employee(client, name="Rounding Worker")
    response = _create_salary(
        client, employee["id"], "2026-07", bonus=100.999, deduction=10.004
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["bonus"] == 101.0
    assert data["deduction"] == 10.0
    # Net is calculated from the rounded amounts.
    assert data["net_salary"] == 20091.0


def test_paid_without_payment_date_defaults_to_today(client):
    employee = _create_employee(client, name="Paid Worker")
    created = _create_salary(client, employee["id"], "2026-06", payment_status="Paid").json()["data"]

    assert created["payment_status"] == "Paid"
    assert created["payment_date"] == date.today().isoformat()


def test_unpaid_has_no_payment_date_and_explicit_date_is_kept(client):
    employee = _create_employee(client, name="Date Worker")

    unpaid = _create_salary(client, employee["id"], "2026-05").json()["data"]
    assert unpaid["payment_date"] is None

    paid = _create_salary(
        client, employee["id"], "2026-04", payment_status="Paid", payment_date="2026-05-03"
    ).json()["data"]
    assert paid["payment_date"] == "2026-05-03"


def test_duplicate_month_for_same_employee_rejected(client):
    employee = _create_employee(client, name="Duplicate Worker")
    first = _create_salary(client, employee["id"], "2026-03")
    duplicate = _create_salary(client, employee["id"], "2026-03")

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert "already exists" in duplicate.json()["message"]

    same_month_other_employee_ok = _create_salary(client, _create_employee(client)["id"], "2026-03")
    assert same_month_other_employee_ok.status_code == 201


def test_update_recalculates_net_salary_and_duplicate_check_excludes_self(client):
    employee = _create_employee(client, name="Update Worker")
    created = _create_salary(client, employee["id"], "2026-02", bonus=0).json()["data"]

    response = client.put(
        f"/api/salaries/{created['id']}",
        json={
            "employee_id": employee["id"],
            "salary_month": "2026-02",
            "base_salary": 21000,
            "bonus": 2000,
            "deduction": 1000,
            "payment_status": "Paid",
            "payment_date": "2026-03-01",
            "notes": "updated run",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["net_salary"] == 22000.0
    assert data["notes"] == "updated run"


def test_deduction_larger_than_base_plus_bonus_rejected(client):
    employee = _create_employee(client, name="Negative Net Worker")
    response = _create_salary(
        client, employee["id"], "2026-02", base_salary=10000, bonus=100, deduction=11000
    )

    assert response.status_code == 422
    body = response.json()
    assert any("negative" in e["message"] for e in body["errors"])


def test_list_ordered_newest_month_first(client):
    employee = _create_employee(client, name="Order Worker")
    _create_salary(client, employee["id"], "2026-01")
    _create_salary(client, employee["id"], "2026-03")
    january_first = client.post(
        "/api/salaries",
        json={"employee_id": employee["id"], "salary_month": "2025-12"},
    )
    assert january_first.status_code == 201

    response = client.get("/api/salaries", params={"employee_id": employee["id"]})
    months = [s["salary_month"] for s in response.json()["data"]["items"]]

    assert months == ["2026-03", "2026-01", "2025-12"]


def test_filters_by_month_and_payment_status(client):
    employee = _create_employee(client, name="Filter Worker")
    paid = _create_salary(client, employee["id"], "2026-02", payment_status="Paid").json()["data"]
    unpaid = _create_salary(client, employee["id"], "2026-03").json()["data"]

    by_month = client.get("/api/salaries", params={"month": "2026-02"}).json()
    ids = [s["id"] for s in by_month["data"]["items"]]
    assert paid["id"] in ids
    assert unpaid["id"] not in ids

    by_status = client.get(
        "/api/salaries", params={"employee_id": employee["id"], "payment_status": "Unpaid"}
    ).json()
    statuses = {s["payment_status"] for s in by_status["data"]["items"]}
    assert statuses == {"Unpaid"}


def test_nonexistent_employee_returns_404(client):
    response = _create_salary(client, 999999, "2026-02")

    assert response.status_code == 404
    assert "not found" in response.json()["message"].lower()


@pytest.mark.parametrize(
    "changes",
    [
        {"salary_month": "08-2026"},
        {"salary_month": "2026-13"},
        {"salary_month": "2026-8"},
        {"salary_month": "abcd-01"},
        {"salary_month": ""},
        {"salary_month": None},
        {"bonus": -1},
        {"bonus": True},
        {"deduction": -50},
        {"base_salary": -100},
        {"payment_status": "Pending"},
        {"employee_id": 0},
        {"employee_id": -3},
        {"employee_id": True},
        {"notes": "x" * 256},
    ],
    ids=[
        "month-reversed-order",
        "month-13",
        "month-not-zero-padded",
        "month-not-a-number",
        "month-empty",
        "month-missing",
        "bonus-negative",
        "bonus-boolean",
        "deduction-negative",
        "base-salary-negative",
        "status-not-allowed",
        "employee-id-zero",
        "employee-id-negative",
        "employee-id-boolean",
        "notes-too-long",
    ],
)
def test_create_with_invalid_data_fails_validation(client, changes):
    payload = {"employee_id": 1, "salary_month": "2026-02"}
    for key, value in changes.items():
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value

    response = client.post("/api/salaries", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert isinstance(body.get("errors"), list) and len(body["errors"]) > 0


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/api/salaries/999999", None),
        ("put", "/api/salaries/999999", {"employee_id": 1, "salary_month": "2026-02"}),
        ("delete", "/api/salaries/999999", None),
    ],
    ids=["get-missing", "put-missing", "delete-missing"],
)
def test_missing_salary_returns_404_envelope(client, method, path, body):
    response = getattr(client, method)(path, json=body) if body else getattr(client, method)(path)

    assert response.status_code == 404
    envelope = response.json()
    assert envelope["success"] is False
    assert "not found" in envelope["message"].lower()


def test_invalid_salary_id_in_path_is_422(client):
    response = client.get("/api/salaries/not-a-number")

    assert response.status_code == 422


def test_delete_salary_then_404_and_employee_delete_unblocked(client):
    employee = _create_employee(client, name="Lifecycle Worker")
    salary = _create_salary(client, employee["id"], "2026-01").json()["data"]

    blocked = client.delete(f"/api/employees/{employee['id']}")
    assert blocked.status_code == 409

    deleted = client.delete(f"/api/salaries/{salary['id']}")
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Salary record deleted."

    unblocked = client.delete(f"/api/employees/{employee['id']}")
    assert unblocked.status_code == 200
