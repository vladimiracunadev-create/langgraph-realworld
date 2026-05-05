"""Tests de la API FastAPI — Caso 17: Legal Intake."""
import json

from fastapi.testclient import TestClient

from src.api import app


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
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
    data = resp.json()
    assert "uptime_s" in data and data["mode"] in ("DEMO", "LIVE")


def test_run_int001_laboral():
    client = TestClient(app)
    resp = client.post("/api/run", json={"thread_id": "test-api-int001", "intake_id": "INT-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["tipo_caso"] == "laboral"
    assert data["urgencia"] == "alta"
    assert data["documento_borrador"] != ""
    assert data["abogado_asignado"].get("especialidad") == "laboral"


def test_run_int003_faltante():
    client = TestClient(app)
    resp = client.post("/api/run", json={"thread_id": "test-api-int003", "intake_id": "INT-003"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["completitud"] == "faltante"
    assert len(data["preguntas_pendientes"]) > 0


def test_run_default():
    resp = TestClient(app).post("/api/run", json={})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_run_invalid_intake_id():
    resp = TestClient(app).post("/api/run", json={"intake_id": "../etc/passwd"})
    assert resp.status_code == 422


def test_stream_returns_ndjson():
    client = TestClient(app)
    resp = client.get("/api/stream?thread_id=test-stream-01&intake_id=INT-001")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")
    lines = [l for l in resp.text.strip().split("\n") if l.strip()]
    assert len(lines) >= 2
    last = json.loads(lines[-1])
    assert last["type"] in ("final", "snapshot", "error")
