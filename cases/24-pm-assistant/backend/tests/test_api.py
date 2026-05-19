"""Tests de la API FastAPI — Caso 24."""
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


def test_run_i001_normal():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-001", "iniciativa_id": "I-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["estado_sprint"] == "normal"
    assert data["estado_final"] == "sprint_en_curso"
    assert len(data["historias"]) == 3


def test_run_i002_impedimento():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-002", "iniciativa_id": "I-002"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["estado_sprint"] == "impedimento"
    assert data["estado_final"] == "sprint_con_impedimento"
    assert len(data["impedimentos"]) >= 1


def test_run_i003_completado():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-003", "iniciativa_id": "I-003"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["estado_sprint"] == "completado"
    assert data["estado_final"] == "sprint_completado"
    assert data["retrospectiva"]["predictibilidad"] >= 0.99


def test_run_i004_fuera_capacidad():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-004", "iniciativa_id": "I-004"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["estado_sprint"] == "normal"
    assert len(data["sprint_asignado"]["fuera_de_capacidad"]) >= 1


def test_run_default():
    resp = TestClient(app).post("/api/run", json={})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_run_invalid_iniciativa_id():
    resp = TestClient(app).post("/api/run", json={"iniciativa_id": "../etc/passwd"})
    assert resp.status_code == 422


def test_stream_returns_ndjson():
    client = TestClient(app)
    resp = client.get("/api/stream?thread_id=t-stream&iniciativa_id=I-001")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")
    lines = [l for l in resp.text.strip().split("\n") if l.strip()]
    assert len(lines) >= 2
    last = json.loads(lines[-1])
    assert last["type"] in ("final", "snapshot", "error")
