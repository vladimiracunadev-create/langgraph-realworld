from fastapi.testclient import TestClient

from src.api import app


def test_healthz():
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
