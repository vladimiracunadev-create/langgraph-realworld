"""Tests de la API FastAPI — Caso 04: SOC Triage de Alertas."""
from fastapi.testclient import TestClient

from src.api import app


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "ts" in data


def test_healthz():
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200


def test_ready():
    client = TestClient(app)
    resp = client.get("/ready")
    assert resp.status_code in (200, 503)


def test_metrics():
    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "uptime_s" in data
    assert "mode" in data
    assert data["mode"] in ("DEMO", "LIVE")


def test_run_alt001():
    """POST /api/run con ALT-001 debe devolver snapshot válido."""
    client = TestClient(app)
    resp = client.post("/api/run", json={"thread_id": "test-api-alt001", "alert_id": "ALT-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert "done" in data
    assert data["done"] is True
    assert "risk_score" in data
    assert "triage_decision" in data
    assert data["triage_decision"] in ("false_positive", "medium", "high")


def test_run_default_params():
    """POST /api/run con defaults debe funcionar."""
    client = TestClient(app)
    resp = client.post("/api/run", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("done") is True


def test_run_invalid_alert_id():
    """alert_id con caracteres inválidos debe rechazarse con 422."""
    client = TestClient(app)
    resp = client.post("/api/run", json={"alert_id": "../etc/passwd"})
    assert resp.status_code == 422
