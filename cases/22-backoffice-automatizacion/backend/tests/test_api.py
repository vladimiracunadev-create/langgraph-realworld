"""Tests de la API FastAPI — Caso 22."""
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


def test_run_sol001_exitosa():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-001", "solicitud_id": "SOL-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["estado_final"] == "exitosa"
    assert data["iter_completitud"] == 0
    assert data["resultado_ejecucion"]["ok"] is True


def test_run_sol002_datos_faltantes_loop():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-002", "solicitud_id": "SOL-002"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["iter_completitud"] >= 1
    assert data["estado_final"] == "exitosa"


def test_run_sol003_sin_permisos_rechazada():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-003", "solicitud_id": "SOL-003"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado_final"] == "rechazada"
    assert data["motivo_rechazo"] == "sin_permiso_para_operacion"


def test_run_sol004_falla_sistema_escalada():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-004", "solicitud_id": "SOL-004"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado_final"] == "escalada"
    assert data["resultado_ejecucion"]["ok"] is False


def test_run_default():
    resp = TestClient(app).post("/api/run", json={})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_run_invalid_solicitud_id():
    resp = TestClient(app).post("/api/run", json={"solicitud_id": "../etc/passwd"})
    assert resp.status_code == 422


def test_stream_returns_ndjson():
    client = TestClient(app)
    resp = client.get("/api/stream?thread_id=t-stream&solicitud_id=SOL-001")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")
    lines = [l for l in resp.text.strip().split("\n") if l.strip()]
    assert len(lines) >= 2
    last = json.loads(lines[-1])
    assert last["type"] in ("final", "snapshot", "error")


def test_log_auditoria_encadenado_sol001():
    resp = TestClient(app).post("/api/run", json={"thread_id": "t-audit", "solicitud_id": "SOL-001"})
    data = resp.json()
    log = data["log_auditoria"]
    assert len(log) >= 4
    # Cadena: prev_hash de cada eslabón = hash del anterior
    prev = "0" * 64
    for eslabon in log:
        assert eslabon["prev_hash"] == prev
        assert len(eslabon["hash"]) == 64
        prev = eslabon["hash"]
    assert data["hash_auditoria"] == prev
