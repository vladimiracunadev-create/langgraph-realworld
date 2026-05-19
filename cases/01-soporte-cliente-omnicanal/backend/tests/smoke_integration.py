from fastapi.testclient import TestClient
from src.api import app


def test_stream_returns_snapshots():
    client = TestClient(app)
    resp = client.get('/api/stream?ticket_id=T-003&thread_id=smoke-01')
    assert resp.status_code == 200
    body = resp.text
    assert 'snapshot' in body
    assert 'final' in body
