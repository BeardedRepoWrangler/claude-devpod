import app as app_module
import pytest
from unittest.mock import patch


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with patch("app.PODMAN_VERSION", "5.0.0-test"), \
         patch("app.OS_NAME", "Test OS 1.0"):
        app_module.REQUEST_LOG.clear()
        with app_module.app.test_client() as c:
            yield c


def test_health_returns_200(client):
    res = client.get("/health")
    assert res.status_code == 200


def test_health_returns_json(client):
    res = client.get("/health")
    data = res.get_json()
    assert data == {"status": "ok"}


def test_request_is_logged_after_call(client):
    client.get("/health")
    assert len(app_module.REQUEST_LOG) == 1
    entry = app_module.REQUEST_LOG[0]
    assert entry["method"] == "GET"
    assert entry["path"] == "/health"
    assert entry["status"] == 200
    assert isinstance(entry["duration_ms"], int)


def test_status_returns_200(client):
    res = client.get("/api/status")
    assert res.status_code == 200


def test_status_response_shape(client):
    res = client.get("/api/status")
    data = res.get_json()
    assert isinstance(data["hostname"], str)
    assert isinstance(data["python_version"], str)
    assert isinstance(data["flask_version"], str)
    assert data["podman_version"] == "5.0.0-test"
    assert data["os"] == "Test OS 1.0"
    assert data["port"] == 8080
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0
    assert isinstance(data["recent_requests"], list)


def test_status_recent_requests_shows_logged_calls(client):
    app_module.REQUEST_LOG.clear()
    client.get("/health")
    res = client.get("/api/status")
    data = res.get_json()
    paths = [r["path"] for r in data["recent_requests"]]
    assert "/health" in paths


def test_index_returns_200(client):
    res = client.get("/")
    assert res.status_code == 200


def test_index_returns_html(client):
    res = client.get("/")
    assert res.content_type.startswith("text/html")
    assert b"<!DOCTYPE html>" in res.data
    assert b"demo-svc" in res.data
