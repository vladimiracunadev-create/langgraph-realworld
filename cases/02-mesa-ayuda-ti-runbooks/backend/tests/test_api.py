import os

from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)


def reset_guards() -> None:
    app.state.rate_limit_buckets.clear()


def test_health():
    reset_guards()
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["mode"] in {"demo", "live"}


def test_run_flow_demo():
    reset_guards()
    response = client.post(
        "/api/run",
        json={"ticket": "VPN intermitente para msmith", "thread_id": "case02-demo-run"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "red"
    assert data["status"] == "RESOLVED"
    assert data["mode"] == "DEMO"
    assert "Reinicio de Servicio VPN" in data["response"]


def test_invalid_thread_id_is_rejected():
    reset_guards()
    response = client.post(
        "/api/run",
        json={"ticket": "VPN intermitente para msmith", "thread_id": "bad id with spaces"},
    )
    assert response.status_code == 422


def test_demo_token_is_optional_and_scoped_to_api(monkeypatch):
    monkeypatch.setenv("DEMO_AUTH_TOKEN", "super-secret-demo-token")
    monkeypatch.delenv("RATE_LIMIT_RPM", raising=False)
    reset_guards()

    health = client.get("/health")
    assert health.status_code == 200

    denied = client.post(
        "/api/run",
        json={"ticket": "VPN intermitente para msmith", "thread_id": "case02-token"},
    )
    assert denied.status_code == 401

    allowed = client.post(
        "/api/run",
        headers={"X-Demo-Token": "super-secret-demo-token"},
        json={"ticket": "VPN intermitente para msmith", "thread_id": "case02-token"},
    )
    assert allowed.status_code == 200


def test_rate_limit_is_enforced_when_enabled(monkeypatch):
    monkeypatch.delenv("DEMO_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("RATE_LIMIT_RPM", "1")
    reset_guards()

    payload = {"ticket": "VPN intermitente para msmith", "thread_id": "case02-rate-limit"}
    first = client.post("/api/run", json=payload)
    second = client.post("/api/run", json=payload)

    assert first.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "1"
    assert second.status_code == 429

    monkeypatch.delenv("RATE_LIMIT_RPM", raising=False)
    os.environ.pop("RATE_LIMIT_RPM", None)
