"""Tests de la API FastAPI — Caso 08: Ventas B2B + CRM."""
import json

from fastapi.testclient import TestClient
from src.api import app


def test_health():
    resp = TestClient(app).get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["mode"] in ("DEMO", "LIVE")


def test_healthz():
    assert TestClient(app).get("/healthz").status_code == 200


def test_ready():
    assert TestClient(app).get("/ready").status_code in (200, 503)


def test_metrics():
    resp = TestClient(app).get("/metrics")
    assert resp.status_code == 200
    assert resp.json()["mode"] in ("DEMO", "LIVE")


def test_run_acc001_meeting():
    client = TestClient(app)
    resp = client.post("/api/run", json={"thread_id": "test-acc001", "account_id": "ACC-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["crm_record"]["deal_stage"] == "Meeting Scheduled"
    assert data["mensaje_outreach"]["cuerpo"]


def test_run_acc003_disqualified():
    client = TestClient(app)
    resp = client.post("/api/run", json={"thread_id": "test-acc003", "account_id": "ACC-003"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["califica"] is False
    assert data["crm_record"]["deal_stage"] == "Disqualified"


def test_run_default():
    resp = TestClient(app).post("/api/run", json={})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_run_invalid_account_id():
    resp = TestClient(app).post("/api/run", json={"account_id": "../etc/passwd"})
    assert resp.status_code == 422


def test_stream_returns_ndjson():
    client = TestClient(app)
    resp = client.get("/api/stream?thread_id=test-stream-01&account_id=ACC-001")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")
    lines = [l for l in resp.text.strip().split("\n") if l.strip()]
    assert len(lines) >= 2
    last = json.loads(lines[-1])
    assert last["type"] in ("final", "snapshot", "error")
