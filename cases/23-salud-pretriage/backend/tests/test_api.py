"""Tests de la API FastAPI — Caso 23 Salud Pre-triage."""
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


def test_run_s001_inmediata():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-s001", "sesion_id": "S-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["nivel_urgencia"] == "inmediata"
    assert data["estado_final"] == "derivado_urgencias"
    assert data["derivacion"]["servicio"] == "urgencias"
    # Disclaimer obligatorio en outputs hacia el paciente
    assert "administrativa" in data["disclaimer"].lower()
    assert "diagnóstico" in data["disclaimer"].lower()
    assert data["disclaimer"] in data["resumen_derivacion"]


def test_run_s002_programable():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-s002", "sesion_id": "S-002"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["nivel_urgencia"] == "programable"
    assert data["estado_final"] == "derivado_especialidad"
    assert data["derivacion"]["servicio"] == "traumatologia"
    assert data["disclaimer"] in data["resumen_derivacion"]


def test_run_s003_teleconsulta():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-s003", "sesion_id": "S-003"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["nivel_urgencia"] == "teleconsulta"
    assert data["estado_final"] == "derivado_teleconsulta"
    assert data["derivacion"]["modalidad"] == "telemedicina"


def test_run_s004_cobertura_pendiente():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-s004", "sesion_id": "S-004"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["cobertura_ok"] is False
    assert data["nivel_urgencia"] == "cobertura_pendiente"
    assert data["estado_final"] == "derivado_documentacion_pendiente"
    assert "credencial_cobertura" in data["documentacion_faltante"]


def test_run_default():
    resp = TestClient(app).post("/api/run", json={})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_run_invalid_sesion_id():
    resp = TestClient(app).post("/api/run", json={"sesion_id": "../etc/passwd"})
    assert resp.status_code == 422


def test_stream_returns_ndjson():
    client = TestClient(app)
    resp = client.get("/api/stream?thread_id=t-stream&sesion_id=S-001")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")
    lines = [l for l in resp.text.strip().split("\n") if l.strip()]
    assert len(lines) >= 2
    last = json.loads(lines[-1])
    assert last["type"] in ("final", "snapshot", "error")
