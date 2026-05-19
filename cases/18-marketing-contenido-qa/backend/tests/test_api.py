"""Tests de la API FastAPI — Caso 18."""
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


def test_run_br001_brief_limpio():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-001", "brief_id": "BR-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["riesgo"] in ("verde", "amarillo")
    assert data["decision_editor"] in ("aprobado", "aprobado_con_observaciones")


def test_run_br002_con_alucinaciones():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-002", "brief_id": "BR-002"})
    assert resp.status_code == 200
    data = resp.json()
    # BR-002 trae claims riesgosos: el agente debe iterar al menos una vez en hechos
    assert data["iter_hechos"] >= 1
    assert data["diff"]["alucinaciones_retiradas"] >= 1


def test_run_br003_landing_legacy():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-003", "brief_id": "BR-003"})
    assert resp.status_code == 200
    data = resp.json()
    # BR-003 trae 3 claims riesgosos
    assert data["iter_hechos"] >= 1


def test_run_default():
    resp = TestClient(app).post("/api/run", json={})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_run_invalid_brief_id():
    resp = TestClient(app).post("/api/run", json={"brief_id": "../etc/passwd"})
    assert resp.status_code == 422


def test_stream_returns_ndjson():
    client = TestClient(app)
    resp = client.get("/api/stream?thread_id=t-stream&brief_id=BR-001")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")
    lines = [l for l in resp.text.strip().split("\n") if l.strip()]
    assert len(lines) >= 2
    last = json.loads(lines[-1])
    assert last["type"] in ("final", "snapshot", "error")


def test_contenido_final_no_vacio():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-md", "brief_id": "BR-001"})
    data = resp.json()
    assert len(data["contenido_final"]) > 100
    assert data["diff"]["palabras_finales"] > 0
    assert data["metricas"]["score_global"] > 0
