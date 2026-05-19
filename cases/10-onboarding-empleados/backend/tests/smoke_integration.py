"""Smoke integration test – Caso 10 (ejecutado en CI via compose.smoke.yml)."""
import os
import sys

import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8010")


def check(name: str, ok: bool, detail: str = "") -> None:
    status = "✅ PASS" if ok else "❌ FAIL"
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        sys.exit(1)


def main():
    print("\n🧪 Smoke Tests – Caso 10: Onboarding de Empleados")
    print(f"   Base URL: {BASE_URL}\n")

    # 1. Health check
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    check("GET /health", r.status_code == 200, r.text)

    # 2. Readiness check
    r = requests.get(f"{BASE_URL}/ready", timeout=5)
    check("GET /ready", r.status_code == 200, r.text)

    # 3. /api/run – ciclo completo
    r = requests.post(
        f"{BASE_URL}/api/run",
        json={"thread_id": "smoke-test-001"},
        timeout=60,
    )
    check("POST /api/run → 200", r.status_code == 200, r.text[:200])
    data = r.json()
    check("done == True", data.get("done") is True)
    check("employee presente", bool(data.get("employee")))
    check("role_type presente", bool(data.get("role_type")))
    check("accounts >= 1", len(data.get("accounts") or []) >= 1)
    check("checklist >= 1 item", len(data.get("checklist") or []) >= 1)
    check("events >= 5", len(data.get("events") or []) >= 5)

    # 4. /api/stream – validación NDJSON
    r = requests.get(f"{BASE_URL}/api/stream?thread_id=smoke-stream-001", timeout=60, stream=True)
    check("GET /api/stream → 200", r.status_code == 200)
    chunks = []
    for line in r.iter_lines():
        if line:
            chunks.append(line)
    check("Stream produjo al menos 3 chunks", len(chunks) >= 3, f"chunks: {len(chunks)}")

    print(f"\n✅ Todos los smoke tests pasaron ({len(chunks)} chunks de stream)\n")


if __name__ == "__main__":
    main()
