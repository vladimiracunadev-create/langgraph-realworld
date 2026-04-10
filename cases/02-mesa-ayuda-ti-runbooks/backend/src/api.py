from __future__ import annotations

import json
import logging
import os
import time
import uuid
from contextvars import ContextVar
from time import monotonic
from typing import Any, Dict

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .auth import auth_middleware, protected_path
from .graph import compile_graph
from .integrations import _is_live
from .settings import backend_root, cors_allowed_origins, load_settings

load_settings()

# ---------------------------------------------------------------------------
# Logging JSON estructurado con trace_id
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
# Métricas en memoria
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
app = FastAPI(title="Caso 02 - Mesa de Ayuda TI")
app.state.rate_limit_buckets = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


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


graph_app = compile_graph()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "mode": "live" if _is_live() else "demo"}


@app.get("/ready")
def ready() -> Dict[str, str]:
    return {"ready": "yes", "case": "02"}


@app.get("/metrics")
def metrics():
    uptime = time.time() - _metrics["start_time"]
    reqs = _metrics["requests"]
    return {
        "uptime_s": round(uptime, 1),
        "requests_total": reqs,
        "errors_total": _metrics["errors"],
        "avg_latency_ms": round(_metrics["latency_sum"] / max(reqs, 1) * 1000, 1),
        "mode": "LIVE" if _is_live() else "DEMO",
        "langsmith_enabled": bool(os.getenv("LANGCHAIN_TRACING_V2", "")),
        "oauth2_enabled": os.getenv("USE_OAUTH2", "false").lower() in {"1", "true", "yes"},
    }


class RunRequest(BaseModel):
    ticket: str = Field(..., min_length=1, max_length=4000)
    thread_id: str = Field(default="demo-thread", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)


@app.post("/api/run")
async def run_ticket(req: RunRequest):
    """Ejecuta el grafo completo (útil para tests sincrónicos)."""
    logger.info("Ejecutando ticket thread_id=%s", req.thread_id)
    initial_state = {"ticket": req.ticket}
    config = {"configurable": {"thread_id": req.thread_id}}
    result = graph_app.invoke(initial_state, config)
    return {
        "status": result.get("resolution_status"),
        "category": result.get("category"),
        "response": result.get("response"),
        "mode": result.get("mode"),
    }


@app.get("/api/stream")
async def stream_ticket(
    ticket: str = Query(..., min_length=1, max_length=4000),
    thread_id: str = Query(default="demo-thread", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN),
):
    """Server-Sent Events / NDJSON endpoint for real-time frontend."""
    async def event_generator():
        initial_state = {"ticket": ticket}
        config = {"configurable": {"thread_id": thread_id}}
        try:
            for s in graph_app.stream(initial_state, config, stream_mode="values"):
                yield f"{json.dumps(s)}\n"
        except Exception as e:
            logger.error("Error en stream: %s", e)
            yield f"{json.dumps({'error': str(e)})}\n"

    return StreamingResponse(event_generator(), media_type="application/ndjson")


# Mount web
web_path = backend_root() / "web"
if web_path.exists():
    app.mount("/web", StaticFiles(directory=str(web_path), html=True), name="web")
