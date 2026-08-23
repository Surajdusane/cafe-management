import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal, engine
from app.main import app
from app.models.cafe_setting import CafeSetting

VALID_PAYLOAD = {
    "cafe_name": "Brew & Bean Cafe",
    "address": "12 Station Road, Pune",
    "phone": "9876543210",
    "email": "hello@brewbean.in",
    "logo_url": "/static/images/favicon.svg",
    "tax_percent": 5.5,
    "currency": "₹",
    "receipt_footer": "Thank you for visiting!",
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def snapshot_original_settings():
    """Capture the pre-test settings row and expose a restore function."""
    with SessionLocal() as db:
        settings = db.get(CafeSetting, 1)
        snapshot = (
            None
            if settings is None
            else {column.name: getattr(settings, column.name) for column in settings.__table__.columns}
        )

    def restore():
        with SessionLocal() as db:
            current = db.get(CafeSetting, 1)
            if snapshot is None:
                if current is not None:
                    db.delete(current)
                    db.commit()
            elif current is not None:
                for field, value in snapshot.items():
                    setattr(current, field, value)
                db.commit()

    return restore


@pytest.fixture(scope="module", autouse=True)
def cleanup(snapshot_original_settings):
    yield
    snapshot_original_settings()


def test_get_settings_returns_success_envelope(client):
    response = client.get("/api/settings")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    expected_keys = {
        "id",
        "cafe_name",
        "address",
        "phone",
        "email",
        "logo_url",
        "tax_percent",
        "currency",
        "receipt_footer",
        "updated_at",
    }
    assert expected_keys.issubset(body["data"].keys())


def test_update_with_valid_data(client):
    response = client.put("/api/settings", json=VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["cafe_name"] == "Brew & Bean Cafe"
    assert data["phone"] == "9876543210"
    assert data["tax_percent"] == 5.5
    assert data["currency"] == "₹"
    assert data["receipt_footer"] == "Thank you for visiting!"


def test_get_reflects_saved_values(client):
    saved = client.get("/api/settings").json()["data"]
    assert saved["cafe_name"] == VALID_PAYLOAD["cafe_name"]


def test_whitespace_trimmed_and_empty_optionals_become_null(client):
    payload = dict(
        VALID_PAYLOAD,
        cafe_name="   Spaced Cafe   ",
        phone="",
        email="",
        address="",
        receipt_footer=None,
    )
    response = client.put("/api/settings", json=payload)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["cafe_name"] == "Spaced Cafe"
    assert data["phone"] is None
    assert data["email"] is None
    assert data["address"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {**VALID_PAYLOAD, "cafe_name": "   "},
        {k: v for k, v in VALID_PAYLOAD.items() if k != "cafe_name"},
        {**VALID_PAYLOAD, "cafe_name": "x" * 101},
        {**VALID_PAYLOAD, "tax_percent": -1},
        {**VALID_PAYLOAD, "tax_percent": 100.5},
        {**VALID_PAYLOAD, "phone": "12345"},
        {**VALID_PAYLOAD, "email": "not-an-email"},
        {**VALID_PAYLOAD, "currency": ""},
        {**VALID_PAYLOAD, "receipt_footer": "x" * 201},
    ],
    ids=[
        "blank-name",
        "missing-name",
        "name-too-long",
        "negative-tax",
        "tax-over-100",
        "invalid-phone",
        "invalid-email",
        "empty-currency",
        "footer-too-long",
    ],
)
def test_update_with_invalid_data_fails_validation(client, payload):
    response = client.put("/api/settings", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert isinstance(body.get("errors"), list) and len(body["errors"]) > 0


def test_failed_update_leaves_saved_values_untouched(client):
    client.put("/api/settings", json=VALID_PAYLOAD)
    response = client.put("/api/settings", json={**VALID_PAYLOAD, "tax_percent": -5})

    assert response.status_code == 422
    saved = client.get("/api/settings").json()["data"]
    assert saved["tax_percent"] == VALID_PAYLOAD["tax_percent"]


def test_settings_persist_after_application_restart():
    with TestClient(app) as first_session_client:
        response = first_session_client.put("/api/settings", json=VALID_PAYLOAD)
        assert response.status_code == 200

    engine.dispose()

    with SessionLocal() as db:
        row = db.get(CafeSetting, 1)
        assert row is not None
        assert row.cafe_name == VALID_PAYLOAD["cafe_name"]

    with TestClient(app) as restarted_client:
        data = restarted_client.get("/api/settings").json()["data"]
        assert data["cafe_name"] == VALID_PAYLOAD["cafe_name"]
        assert data["tax_percent"] == VALID_PAYLOAD["tax_percent"]
