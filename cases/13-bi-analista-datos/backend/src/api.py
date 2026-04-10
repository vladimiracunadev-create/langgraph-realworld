from __future__ import annotations

import json
import logging
import os
import time
import uuid
from contextvars import ContextVar
from time import monotonic
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .auth import auth_middleware, protected_path
from .graph import EXAMPLE_QUESTIONS, IS_DEMO_MODE, graph
from .settings import settings

# ---------------------------------------------------------------------------
# Logging JSON estructurado con trace_id
# ---------------------------------------------------------------------------
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="system")


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
app = FastAPI(title="Case 13: BI Data Analyst")
app.state.rate_limit_buckets = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

if settings.web_dir.exists():
    app.mount("/web", StaticFiles(directory=str(settings.web_dir), html=True), name="web")
shared_assets_dir = settings.web_dir.parents[2] / "assets"
if shared_assets_dir.exists():
    app.mount("/shared-assets", StaticFiles(directory=str(shared_assets_dir)), name="shared-assets")


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


def app_metadata() -> dict[str, Any]:
    return {
        "mode": "DEMO" if IS_DEMO_MODE else "LIVE",
        "database_ready": settings.database_path.exists(),
        "web_ready": settings.web_dir.exists(),
        "examples": EXAMPLE_QUESTIONS,
    }


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


@app.get("/health")
async def health():
    return {"status": "ok", "port": settings.PORT, **app_metadata()}


@app.get("/ready")
async def ready():
    if not settings.database_path.exists():
        raise HTTPException(status_code=503, detail=f"Database not found: {settings.database_path}")
    if not settings.web_dir.exists():
        raise HTTPException(status_code=503, detail=f"Web directory not found: {settings.web_dir}")
    return {"status": "ready", **app_metadata()}


@app.get("/examples")
async def examples():
    return app_metadata()


@app.get("/metrics")
async def metrics():
    uptime = time.time() - _metrics["start_time"]
    reqs = _metrics["requests"]
    return {
        "uptime_s": round(uptime, 1),
        "requests_total": reqs,
        "errors_total": _metrics["errors"],
        "avg_latency_ms": round(_metrics["latency_sum"] / max(reqs, 1) * 1000, 1),
        "mode": "DEMO" if IS_DEMO_MODE else "LIVE",
        "langsmith_enabled": bool(os.getenv("LANGCHAIN_TRACING_V2", "")),
        "oauth2_enabled": os.getenv("USE_OAUTH2", "false").lower() in {"1", "true", "yes"},
    }


@app.post("/chat")
async def chat(payload: ChatRequest):
    question = payload.question.strip()
    logger.info("Chat question received")

    async def event_generator():
        inputs = {"question": question}
        async for output in graph.astream(inputs, stream_mode="values"):
            event_payload = {**output, "mode": "DEMO" if IS_DEMO_MODE else "LIVE"}
            yield f"data: {json.dumps(event_payload, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/")
async def root():
    return {
        "message": "Case 13: BI Data Analyst API is running",
        **app_metadata(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
