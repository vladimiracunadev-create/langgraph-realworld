"""Tests de la API FastAPI — Caso 06."""
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


def test_run_aud001_clean():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-001", "audit_id": "AUD-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["riesgo"] == "verde"
    assert data["score_cumplimiento"] == 100


def test_run_aud002_faltantes():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-002", "audit_id": "AUD-002"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["riesgo"] in ("amarillo", "rojo")
    assert len(data["escalaciones"]) >= 1


def test_run_aud003_gdpr_vencido():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-003", "audit_id": "AUD-003"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["invalidas"]) >= 1


def test_run_default():
    resp = TestClient(app).post("/api/run", json={})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_run_invalid_audit_id():
    resp = TestClient(app).post("/api/run", json={"audit_id": "../etc/passwd"})
    assert resp.status_code == 422


def test_stream_returns_ndjson():
    client = TestClient(app)
    resp = client.get("/api/stream?thread_id=t-stream&audit_id=AUD-001")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")
    lines = [l for l in resp.text.strip().split("\n") if l.strip()]
    assert len(lines) >= 2
    last = json.loads(lines[-1])
    assert last["type"] in ("final", "snapshot", "error")


def test_trazabilidad_en_response():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-traza", "audit_id": "AUD-001"})
    data = resp.json()
    traza = data["trazabilidad"]
    assert len(traza) >= 6
    assert traza[0]["prev_hash"] == "GENESIS"
    for i in range(1, len(traza)):
        assert traza[i]["prev_hash"] == traza[i - 1]["hash"]
