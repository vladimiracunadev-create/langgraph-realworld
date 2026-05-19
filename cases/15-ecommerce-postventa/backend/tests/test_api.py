"""Tests de la API FastAPI — Caso 15."""
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


def test_run_ord001_seguimiento():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-001", "order_id": "ORD-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["intencion"] == "seguimiento"
    assert data["tracking"]["encontrado"] is True


def test_run_ord002_devolucion_elegible():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-002", "order_id": "ORD-002"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["etiqueta"]["emitida"] is True


def test_run_ord003_escalado():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-003", "order_id": "ORD-003"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["escalacion"]["requerida"] is True


def test_run_ord005_cambio_sin_stock_escala():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-005", "order_id": "ORD-005"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["escalacion"]["requerida"] is True


def test_run_default():
    resp = TestClient(app).post("/api/run", json={})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_run_invalid_order_id():
    resp = TestClient(app).post("/api/run", json={"order_id": "../etc/passwd"})
    assert resp.status_code == 422


def test_run_invalid_intent():
    resp = TestClient(app).post("/api/run", json={"order_id": "ORD-001", "intent": "ruido"})
    assert resp.status_code == 422


def test_stream_returns_ndjson():
    client = TestClient(app)
    resp = client.get("/api/stream?thread_id=t-stream&order_id=ORD-001")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")
    lines = [l for l in resp.text.strip().split("\n") if l.strip()]
    assert len(lines) >= 2
    last = json.loads(lines[-1])
    assert last["type"] in ("final", "snapshot", "error")
