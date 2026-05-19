"""Tests de la API FastAPI — Caso 16."""
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


def test_run_v001_aprobado_primer_intento():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-001", "viaje_id": "V-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["estado_final"] == "aprobado"
    assert data["iter_optimizacion"] == 0
    assert data["iter_ajuste"] == 0
    assert data["dentro_presupuesto"] is True


def test_run_v002_optimiza_costos():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-002", "viaje_id": "V-002"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["estado_final"] == "aprobado"
    assert data["iter_optimizacion"] >= 1
    assert data["dentro_presupuesto"] is True


def test_run_v003_aplica_ajuste_viajero():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-003", "viaje_id": "V-003"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["estado_final"] == "aprobado"
    assert data["iter_ajuste"] >= 1


def test_run_v004_rechazado_por_politica():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-004", "viaje_id": "V-004"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado_final"] == "rechazado"
    assert data["politica_ok"] is False
    assert data["motivo_rechazo"] == "ciudad_restringida_por_politica"


def test_run_default():
    resp = TestClient(app).post("/api/run", json={})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_run_invalid_viaje_id():
    resp = TestClient(app).post("/api/run", json={"viaje_id": "../etc/passwd"})
    assert resp.status_code == 422


def test_stream_returns_ndjson():
    client = TestClient(app)
    resp = client.get("/api/stream?thread_id=t-stream&viaje_id=V-001")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")
    lines = [l for l in resp.text.strip().split("\n") if l.strip()]
    assert len(lines) >= 2
    last = json.loads(lines[-1])
    assert last["type"] in ("final", "snapshot", "error")


def test_auditoria_no_vacia_v001():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-audit", "viaje_id": "V-001"})
    data = resp.json()
    audit = data["audit_trail"]
    assert len(audit) >= 5
    types = [a["type"] for a in audit]
    assert "requisitos_parseados" in types
    assert "brief_generado" in types
