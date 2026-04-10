from fastapi.testclient import TestClient

from src.api import app


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "ts" in data


def test_ready():
    client = TestClient(app)
    resp = client.get("/ready")
    # Puede ser 200 (ready) o 503 (no listo) dependiendo del entorno
    assert resp.status_code in (200, 503)


def test_metrics():
    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "uptime_s" in data


def test_run():
    client = TestClient(app)
    resp = client.post("/api/run", json={"thread_id": "test-thread-1", "incident_id": "INC-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert "done" in data
