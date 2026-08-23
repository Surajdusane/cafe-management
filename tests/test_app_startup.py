import pytest
from fastapi.testclient import TestClient

from app.main import PAGES, app

from pathlib import Path


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint_reports_ok(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["database"] == "connected"
    assert body["data"]["app_name"] == "Cafe Management System"


@pytest.mark.parametrize("route", list(PAGES.keys()))
def test_every_page_route_serves_html(client, route):
    response = client.get(route)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_dashboard_page_markers(client):
    response = client.get("/")

    assert response.status_code == 200
    html = response.text
    assert 'data-page="dashboard"' in html
    assert "/static/js/common.js" in html


def test_navigation_config_covers_all_pages():
    common_js = Path(__file__).resolve().parent.parent / "static" / "js" / "common.js"
    source = common_js.read_text(encoding="utf-8")

    for route in PAGES:
        if route != "/":
            assert f'"{route}"' in source


def test_unknown_api_route_returns_error_envelope(client):
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert "message" in body


def test_static_assets_are_served(client):
    css = client.get("/static/css/main.css")
    js = client.get("/static/js/common.js")

    assert css.status_code == 200
    assert "text/css" in css.headers["content-type"]
    assert js.status_code == 200


def test_favicon_is_served(client):
    response = client.get("/static/images/favicon.svg")

    assert response.status_code == 200
