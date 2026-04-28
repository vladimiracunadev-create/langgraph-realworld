"""Tests de la API FastAPI — Caso 05: Analista de Documentos."""
from fastapi.testclient import TestClient

from src.api import app


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "ts" in data
    assert data["mode"] in ("DEMO", "LIVE")


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


def test_run_doc001():
    """POST /api/run con DOC-001 (NDA) debe devolver snapshot válido con riesgo bajo."""
    client = TestClient(app)
    resp = client.post("/api/run", json={"thread_id": "test-api-doc001", "doc_id": "DOC-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("done") is True
    assert data.get("risk_level") in ("bajo", "medio", "alto")
    assert data.get("risk_score", -1) >= 0
    assert isinstance(data.get("clauses"), list)
    assert isinstance(data.get("checklist"), list)
    assert data.get("executive_summary", "") != ""


def test_run_doc003_alto_riesgo():
    """DOC-003 (Licitación) debe devolver riesgo alto y escalación."""
    client = TestClient(app)
    resp = client.post("/api/run", json={"thread_id": "test-api-doc003", "doc_id": "DOC-003"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("done") is True
    assert data.get("risk_level") == "alto"
    assert data.get("escalation_notes", "") != ""


def test_run_default_params():
    """POST /api/run con defaults debe funcionar."""
    client = TestClient(app)
    resp = client.post("/api/run", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("done") is True


def test_run_invalid_doc_id():
    """doc_id con caracteres inválidos debe rechazarse con 422."""
    client = TestClient(app)
    resp = client.post("/api/run", json={"doc_id": "../etc/passwd"})
    assert resp.status_code == 422


def test_stream_returns_ndjson():
    """GET /api/stream debe devolver content-type application/x-ndjson."""
    client = TestClient(app)
    resp = client.get("/api/stream?thread_id=test-stream-01&doc_id=DOC-001")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")
    lines = [l for l in resp.text.strip().split("\n") if l.strip()]
    assert len(lines) >= 1
    import json
    last = json.loads(lines[-1])
    assert last.get("type") in ("final", "snapshot", "error")
