"""Tests de la API FastAPI — Caso 07."""
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


def test_run_pr001_aprobada():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-001", "solicitud_id": "PR-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["aprobacion"]["estado"] == "APROBADA"
    assert data["orden_compra"]["emitida"] is True


def test_run_pr003_condicional():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-003", "solicitud_id": "PR-003"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["aprobacion"]["estado"] == "CONDICIONAL"
    assert data["escalacion_comite"]["requerida"] is True


def test_run_default():
    resp = TestClient(app).post("/api/run", json={})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_run_invalid_solicitud_id():
    resp = TestClient(app).post("/api/run", json={"solicitud_id": "../etc/passwd"})
    assert resp.status_code == 422


def test_stream_returns_ndjson():
    client = TestClient(app)
    resp = client.get("/api/stream?thread_id=t-stream&solicitud_id=PR-001")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")
    lines = [l for l in resp.text.strip().split("\n") if l.strip()]
    assert len(lines) >= 2
    last = json.loads(lines[-1])
    assert last["type"] in ("final", "snapshot", "error")
