"""
test_api.py — Tests de integración para la API FastAPI del caso 19.

Verifica que los endpoints básicos respondan correctamente en modo DEMO.
No requiere OPENAI_API_KEY ni GITHUB_TOKEN.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Crea un TestClient para la app FastAPI."""
    from src.api import app
    return TestClient(app, raise_server_exceptions=True)


def test_health(client):
    """GET /health debe devolver 200 con status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "ts" in body


def test_healthz(client):
    """GET /healthz debe ser alias de /health."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics(client):
    """GET /metrics debe devolver 200 con campo uptime_s."""
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "uptime_s" in body
    assert isinstance(body["uptime_s"], (int, float))
    assert body["uptime_s"] >= 0
    assert "requests_total" in body
    assert "mode" in body
    assert body["mode"] in ("DEMO", "LIVE")


def test_ready(client):
    """GET /ready debe devolver 200 cuando el grafo compila correctamente."""
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_run(client):
    """
    POST /api/run debe devolver 200 con los campos de revisión del PR.
    Verifica la presencia de 'done' y 'decision' en la respuesta.
    """
    payload = {"thread_id": "test-run-001", "pr_id": "PR-001"}
    response = client.post("/api/run", json=payload)
    assert response.status_code == 200, f"Error: {response.text}"
    body = response.json()

    # Campos obligatorios en la respuesta
    assert "done" in body, "Falta campo 'done' en la respuesta"
    assert "decision" in body, "Falta campo 'decision' en la respuesta"
    assert body["done"] is True, "El grafo debe terminar con done=True"
    assert body["decision"] in (
        "request_changes",
        "approve_with_comments",
        "approve",
    ), f"Decisión inesperada: {body['decision']}"

    # Campos de análisis
    assert "all_findings" in body
    assert isinstance(body["all_findings"], list)
    assert "risk_level" in body
    assert body["risk_level"] in ("high", "medium", "low")
    assert "changelog" in body
    assert isinstance(body["changelog"], str)


def test_run_default_pr_id(client):
    """POST /api/run sin pr_id explícito debe usar el valor por defecto."""
    payload = {"thread_id": "test-run-default"}
    response = client.post("/api/run", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "decision" in body
    assert "done" in body


def test_run_invalid_thread_id(client):
    """POST /api/run con thread_id inválido debe devolver 422."""
    payload = {"thread_id": "invalid id with spaces!", "pr_id": "PR-001"}
    response = client.post("/api/run", json=payload)
    assert response.status_code == 422


def test_x_trace_id_header(client):
    """Las respuestas deben incluir el header X-Trace-ID."""
    response = client.get("/health")
    assert "x-trace-id" in response.headers or "X-Trace-ID" in response.headers
