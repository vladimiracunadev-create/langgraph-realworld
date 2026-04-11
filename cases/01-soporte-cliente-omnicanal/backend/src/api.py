from __future__ import annotations

import json
import logging
import os
import time
import uuid
from contextvars import ContextVar
from functools import lru_cache
from pathlib import Path
from time import monotonic
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .auth import auth_middleware, protected_path
from .graph import compile_graph
from .settings import data_dir, host, mode_label, port, web_dir

# ---------------------------------------------------------------------------
# Logging JSON estructurado con trace_id propagado por ContextVar
# ---------------------------------------------------------------------------
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="system")
SAFE_ID_PATTERN = r"^[A-Za-z0-9._:-]{1,64}$"


class TraceIdFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = trace_id_var.get()
        return True


LOG_FORMAT = (
    '{"ts": "%(asctime)s", "level": "%(levelname)s", '
    '"name": "%(name)s", "msg": "%(message)s", "trace_id": "%(trace_id)s"}'
)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logging.getLogger().addFilter(TraceIdFilter())
logger = logging.getLogger("api")

# ---------------------------------------------------------------------------
# Métricas en memoria (simples, sin dependencias externas)
# ---------------------------------------------------------------------------
_metrics: dict[str, Any] = {
    "requests": 0,
    "errors": 0,
    "latency_sum": 0.0,
    "start_time": time.time(),
}

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Caso 01 - Soporte cliente omnicanal")
app.state.rate_limit_buckets = {}

WEB_DIR = web_dir()
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
SHARED_ASSETS_DIR = Path(__file__).resolve().parents[4] / "assets"
if SHARED_ASSETS_DIR.exists():
    app.mount("/shared-assets", StaticFiles(directory=str(SHARED_ASSETS_DIR)), name="shared-assets")


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


# ---------------------------------------------------------------------------
# Middleware: trace_id + auth + rate-limit + métricas
# ---------------------------------------------------------------------------
@app.middleware("http")
async def observability_and_guards(request: Request, call_next):
    request_id = str(uuid.uuid4())
    ctx_token = trace_id_var.set(request_id)
    t0 = monotonic()
    try:
        response = await auth_middleware(
            request, call_next,
            rate_limit_buckets=app.state.rate_limit_buckets,
            trace_id=request_id,
        )
        if protected_path(request.url.path):
            _metrics["requests"] += 1
            if response.status_code >= 500:
                _metrics["errors"] += 1
            _metrics["latency_sum"] += monotonic() - t0
        response.headers["X-Trace-ID"] = request_id
        return response
    finally:
        trace_id_var.reset(ctx_token)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
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


@app.get("/metrics")
def metrics():
    uptime = time.time() - _metrics["start_time"]
    reqs = _metrics["requests"]
    return {
        "uptime_s": round(uptime, 1),
        "requests_total": reqs,
        "errors_total": _metrics["errors"],
        "avg_latency_ms": round(_metrics["latency_sum"] / max(reqs, 1) * 1000, 1),
        "mode": mode_label(),
        "langsmith_enabled": bool(os.getenv("LANGCHAIN_TRACING_V2", "")),
        "oauth2_enabled": os.getenv("USE_OAUTH2", "false").lower() in {"1", "true", "yes"},
    }


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


class RunIn(BaseModel):
    thread_id: str = Field(default="support-demo-01", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)
    ticket_id: str = Field(default="T-001", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)
    ticket: dict[str, Any] | None = None


@app.post("/api/run")
def run(payload: RunIn):
    graph = get_graph()
    cfg = {"configurable": {"thread_id": payload.thread_id}, "recursion_limit": 20}
    logger.info("Iniciando ejecucion para thread_id: %s", payload.thread_id)
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
        logger.error("Error en /api/run: %s", exc)
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
            input_data = {"request": {"ticket_id": ticket_id}, "events": []}
            for state in graph.stream(input_data, config=cfg, stream_mode="values"):
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
                payload = json.dumps({"type": "snapshot", "snapshot": snapshot}, ensure_ascii=False)
                yield (payload + "\n").encode("utf-8")
            yield (json.dumps({"type": "final", "ok": True}) + "\n").encode("utf-8")
        except Exception as exc:
            logger.error("Error en stream: %s", exc)
            yield (json.dumps({"type": "error", "detail": str(exc)}) + "\n").encode("utf-8")

    return StreamingResponse(gen(), media_type="application/x-ndjson")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=host(), port=port())
