"""
test_api.py — Tests de los endpoints FastAPI del caso 25.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from src.api import app
    return TestClient(app)


def test_health(client):
    """GET /health debe retornar 200 con status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ts" in data


def test_healthz(client):
    """GET /healthz debe retornar 200."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics(client):
    """GET /metrics debe retornar 200 con campos esperados."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_s" in data
    assert "requests_total" in data
    assert "errors_total" in data
    assert "mode" in data
    assert data["mode"] == "DEMO"


def test_ready(client):
    """GET /ready debe retornar 200 si el grafo compila correctamente."""
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_run(client):
    """POST /api/run debe retornar 200 con done=True y final_report no vacío."""
    payload = {"thread_id": "test-run-1", "task_id": "DDL-2026-001"}
    response = client.post("/api/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["done"] is True
    assert "final_report" in data
    assert len(data["final_report"]) > 0
    assert "worker_results" in data
    assert len(data["worker_results"]) == 4
    assert "task_id" in data
    assert data["task_id"] == "DDL-2026-001"


def test_run_default_task_id(client):
    """POST /api/run con task_id por defecto debe funcionar correctamente."""
    payload = {"thread_id": "test-run-default"}
    response = client.post("/api/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["done"] is True
