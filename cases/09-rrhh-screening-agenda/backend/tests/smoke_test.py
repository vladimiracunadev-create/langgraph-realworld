import requests
import json
import time
import sys
import os

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

def test_health():
    print("Testing /health...")
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    print("✅ /health ok")

def test_ready():
    print("Testing /ready...")
    resp = requests.get(f"{BASE_URL}/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"
    print("✅ /ready ok")

def test_run():
    print("Testing /api/run...")
    resp = requests.post(f"{BASE_URL}/api/run", json={"thread_id": "smoke-test-thread"})
    assert resp.status_code == 200
    data = resp.json()
    assert "job" in data
    assert data["done"] is True
    print("✅ /api/run ok")

def test_stream():
    print("Testing /api/stream...")
    resp = requests.get(f"{BASE_URL}/api/stream", params={"thread_id": "smoke-test-stream"}, stream=True)
    assert resp.status_code == 200
    
    found_snapshot = False
    found_final = False
    
    for line in resp.iter_lines():
        if line:
            chunk = json.loads(line.decode("utf-8"))
            if chunk["type"] == "snapshot":
                found_snapshot = True
            if chunk["type"] == "final":
                found_final = True
                break
    
    assert found_snapshot, "No snapshot found in stream"
    assert found_final, "Final event not found in stream"
    print("✅ /api/stream ok")

if __name__ == "__main__":
    try:
        test_health()
        test_ready()
        test_run()
        test_stream()
        print("\n🚀 All smoke tests passed!")
    except Exception as e:
        print(f"\n❌ Smoke test failed: {e}")
        sys.exit(1)
