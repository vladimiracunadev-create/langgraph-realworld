"""Tests de la API FastAPI — Caso 12."""
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


def test_run_inst_comp_dig():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-cd", "instrument_id": "INST-COMP-DIG-01"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["psicometria"]["alpha_cronbach"] > 0
    assert data["n_evaluados"] == 40


def test_run_inst_raz_log():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-rl", "instrument_id": "INST-RAZ-LOG-02"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["iteracion_validez"] >= 1


def test_run_inst_esc_bie():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-bl", "instrument_id": "INST-ESC-BIE-03"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["instrument"]["formato"] == "likert"


def test_run_default():
    resp = TestClient(app).post("/api/run", json={})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_run_invalid_instrument_id():
    resp = TestClient(app).post("/api/run", json={"instrument_id": "../etc/passwd"})
    assert resp.status_code == 422


def test_stream_returns_ndjson():
    client = TestClient(app)
    resp = client.get("/api/stream?thread_id=t-stream&instrument_id=INST-COMP-DIG-01")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")
    lines = [l for l in resp.text.strip().split("\n") if l.strip()]
    assert len(lines) >= 2
    last = json.loads(lines[-1])
    assert last["type"] in ("final", "snapshot", "error")
