from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)


def test_health():
    resp = client.get('/health')
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'ok'
    assert data['mode'] in {'DEMO', 'LIVE'}


def test_run_flow():
    resp = client.post('/api/run', json={'ticket_id': 'T-002', 'thread_id': 'test-case01'})
    assert resp.status_code == 200
    data = resp.json()
    assert data['ticket']['ticket_id'] == 'T-002'
    assert data['intent'] == 'billing'
    assert data['done'] is True
    assert len(data['actions']) >= 1
