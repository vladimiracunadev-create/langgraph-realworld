from __future__ import annotations

import json
import os
import time
from collections import deque
from functools import lru_cache
from hmac import compare_digest
from pathlib import Path
from time import monotonic
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .graph import compile_graph
from .settings import data_dir, host, mode_label, port, web_dir

app = FastAPI(title="Caso 01 - Soporte cliente omnicanal")
app.state.rate_limit_buckets = {}

WEB_DIR = web_dir()
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
SHARED_ASSETS_DIR = Path(__file__).resolve().parents[4] / "assets"
if SHARED_ASSETS_DIR.exists():
    app.mount("/shared-assets", StaticFiles(directory=str(SHARED_ASSETS_DIR)), name="shared-assets")

SAFE_ID_PATTERN = r"^[A-Za-z0-9._:-]{1,64}$"


class RunIn(BaseModel):
    thread_id: str = Field(default="support-demo-01", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)
    ticket_id: str = Field(default="T-001", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)
    ticket: dict[str, Any] | None = None


@lru_cache(maxsize=1)
def get_graph():
    return compile_graph()


def metadata() -> dict[str, Any]:
    return {
        "mode": mode_label(),
        "port": port(),
        "data_ready": data_dir().exists(),
        "web_ready": WEB_DIR.exists(),
    }


def demo_auth_token() -> str:
    return os.getenv("DEMO_AUTH_TOKEN", "").strip()


def rate_limit_rpm() -> int:
    raw = os.getenv("RATE_LIMIT_RPM", "0").strip()
    try:
        return max(int(raw), 0)
    except ValueError:
        return 0


def trust_proxy_headers() -> bool:
    return os.getenv("TRUST_PROXY_HEADERS", "false").strip().lower() in {"1", "true", "yes", "on"}


def protected_path(path: str) -> bool:
    return path.startswith("/api/")


def client_identity(request: Request) -> str:
    if trust_proxy_headers():
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for.strip():
            return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@app.middleware("http")
async def enforce_demo_guards(request: Request, call_next):
    limit = rate_limit_rpm()

    if protected_path(request.url.path):
        token = demo_auth_token()
        if token:
            provided = request.headers.get("x-demo-token", "").strip()
            if not compare_digest(provided, token):
                return JSONResponse(status_code=401, content={"detail": "Missing or invalid X-Demo-Token"})

        if limit > 0:
            now = monotonic()
            bucket = app.state.rate_limit_buckets.setdefault(client_identity(request), deque())
            while bucket and now - bucket[0] >= 60:
                bucket.popleft()
            if len(bucket) >= limit:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
            bucket.append(now)

    response = await call_next(request)
    if limit > 0 and protected_path(request.url.path):
        bucket = app.state.rate_limit_buckets.get(client_identity(request), deque())
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(limit - len(bucket), 0))
    return response


@app.get("/health")
def health():
    return {"status": "ok", "ts": int(time.time()), **metadata()}


@app.get("/healthz")
def healthz():
    return health()


@app.get("/ready")
def ready():
    if not data_dir().exists():
        raise HTTPException(status_code=503, detail="Data directory not found")
    if not WEB_DIR.exists():
        raise HTTPException(status_code=503, detail="Web directory not found")
    _ = get_graph()
    return {"status": "ready", **metadata()}


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>UI no disponible</h1>", status_code=404)
    html = index_path.read_text(encoding="utf-8")
    html = html.replace(
        "<body>",
        '<body data-api-config-cases="01" data-api-config-title="APIs del Caso 01">',
        1,
    )
    html = html.replace(
        "</body>",
        '  <script src="/shared-assets/api-config.js"></script>\n</body>',
        1,
    )
    return html


@app.post("/api/run")
def run(payload: RunIn):
    graph = get_graph()
    cfg = {"configurable": {"thread_id": payload.thread_id}, "recursion_limit": 20}
    try:
        out = graph.invoke({"request": payload.model_dump(), "events": []}, config=cfg)
        snapshot = {
            "ticket": out.get("ticket") or {},
            "intent": out.get("intent") or "",
            "priority": out.get("priority") or "",
            "route": out.get("route") or {},
            "knowledge": out.get("knowledge") or {},
            "actions": out.get("actions") or [],
            "response": out.get("response") or "",
            "events": out.get("events") or [],
            "done": bool(out.get("done", False)),
            "mode": out.get("mode") or mode_label(),
        }
        return JSONResponse(snapshot)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/stream")
def stream(
    ticket_id: str = Query(default="T-001", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN),
    thread_id: str = Query(default="support-demo-01", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN),
):
    graph = get_graph()
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}

    def gen():
        try:
            for state in graph.stream({"request": {"ticket_id": ticket_id}, "events": []}, config=cfg, stream_mode="values"):
                snapshot = {
                    "ticket": state.get("ticket") or {},
                    "intent": state.get("intent") or "",
                    "priority": state.get("priority") or "",
                    "route": state.get("route") or {},
                    "knowledge": state.get("knowledge") or {},
                    "actions": state.get("actions") or [],
                    "response": state.get("response") or "",
                    "events": state.get("events") or [],
                    "done": bool(state.get("done", False)),
                    "mode": state.get("mode") or mode_label(),
                }
                yield (json.dumps({"type": "snapshot", "snapshot": snapshot}, ensure_ascii=False) + "\n").encode("utf-8")
            yield (json.dumps({"type": "final", "ok": True}) + "\n").encode("utf-8")
        except Exception as exc:
            yield (json.dumps({"type": "error", "detail": str(exc)}) + "\n").encode("utf-8")

    return StreamingResponse(gen(), media_type="application/x-ndjson")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=host(), port=port())
