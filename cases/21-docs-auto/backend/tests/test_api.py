"""Tests de la API FastAPI — Caso 21."""
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


def test_run_doc001_clean():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-001", "repo_id": "DOC-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["riesgo"] == "verde"
    assert data["score_global"] >= 90


def test_run_doc002_partial():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-002", "repo_id": "DOC-002"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["issues"]) >= 2  # endpoints sin doc + tests fallando


def test_run_doc003_legacy():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-003", "repo_id": "DOC-003"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["iter_revision"] >= 1


def test_run_default():
    resp = TestClient(app).post("/api/run", json={})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_run_invalid_repo_id():
    resp = TestClient(app).post("/api/run", json={"repo_id": "../etc/passwd"})
    assert resp.status_code == 422


def test_stream_returns_ndjson():
    client = TestClient(app)
    resp = client.get("/api/stream?thread_id=t-stream&repo_id=DOC-001")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")
    lines = [l for l in resp.text.strip().split("\n") if l.strip()]
    assert len(lines) >= 2
    last = json.loads(lines[-1])
    assert last["type"] in ("final", "snapshot", "error")


def test_documento_md_no_vacio():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-md", "repo_id": "DOC-001"})
    data = resp.json()
    assert len(data["documento_md"]) > 200
    assert data["diff"]["secciones_agregadas"] > 0
