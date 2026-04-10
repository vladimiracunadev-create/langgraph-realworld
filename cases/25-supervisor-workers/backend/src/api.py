"""
api.py — FastAPI para Caso 25: Supervisor-Workers Due Diligence.

Endpoints:
  GET  /health, /healthz, /ready, /metrics
  POST /api/run    — ejecuta el flujo y retorna snapshot final
  GET  /api/stream — streaming NDJSON del flujo
"""
import json
import logging
import os
import time
import uuid
from contextvars import ContextVar
from functools import lru_cache
from time import monotonic

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from .auth import auth_middleware, protected_path
from .graph import compile_graph

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="system")
SAFE_ID_PATTERN = r"^[A-Za-z0-9._:-]{1,64}$"


class TraceIdFilter(logging.Filter):
    """Filtro para inyectar el trace_id actual en cada registro de log."""

    def filter(self, record):
        record.trace_id = trace_id_var.get()
        return True


LOG_FORMAT = (
    '{"ts": "%(asctime)s", "level": "%(levelname)s", '
    '"name": "%(name)s", "msg": "%(message)s", "trace_id": "%(trace_id)s"}'
)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
root_logger = logging.getLogger()
root_logger.addFilter(TraceIdFilter())
logger = logging.getLogger("api")

_metrics: dict = {"requests": 0, "errors": 0, "latency_sum": 0.0, "start_time": time.time()}

app = FastAPI(title="Caso 25 - Supervisor Workers (Due Diligence)")
app.state.rate_limit_buckets = {}


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


@lru_cache(maxsize=1)
def get_graph():
    """Compila el grafo SOLO cuando se necesita (evita romper pytest/CI al importar)."""
    return compile_graph()


@app.get("/health")
def health():
    """Liveness check."""
    return {"status": "ok", "ts": int(time.time())}


@app.get("/healthz")
def healthz():
    return health()


@app.get("/ready")
def ready():
    """Readiness check: verifica si el grafo compila."""
    try:
        _ = get_graph()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/metrics")
def metrics():
    uptime = time.time() - _metrics["start_time"]
    reqs = _metrics["requests"]
    return {
        "uptime_s": round(uptime, 1),
        "requests_total": reqs,
        "errors_total": _metrics["errors"],
        "avg_latency_ms": round(_metrics["latency_sum"] / max(reqs, 1) * 1000, 1),
        "mode": "LIVE" if os.getenv("OPENAI_API_KEY", "").strip() else "DEMO",
        "langsmith_enabled": bool(os.getenv("LANGCHAIN_TRACING_V2", "")),
        "oauth2_enabled": os.getenv("USE_OAUTH2", "false").lower() in {"1", "true", "yes"},
    }


class RunIn(BaseModel):
    thread_id: str = Field(
        default="ddl-demo-1",
        min_length=1,
        max_length=64,
        pattern=SAFE_ID_PATTERN,
    )
    task_id: str = Field(
        default="DDL-2026-001",
        min_length=1,
        max_length=64,
    )


@app.post("/api/run")
def run(payload: RunIn):
    """Ejecuta el flujo de due diligence y devuelve snapshot final."""
    logger.info(f"Iniciando ejecucion para thread_id={payload.thread_id} task_id={payload.task_id}")
    start_time = time.time()
    try:
        graph = get_graph()
        cfg = {"configurable": {"thread_id": payload.thread_id}, "recursion_limit": 50}
        out = graph.invoke({"task_id": payload.task_id, "events": []}, config=cfg)

        snapshot = {
            "task_id": out.get("task_id", "") if isinstance(out, dict) else "",
            "task": out.get("task", {}) if isinstance(out, dict) else {},
            "worker_results": out.get("worker_results", []) if isinstance(out, dict) else [],
            "conflicts": out.get("conflicts", []) if isinstance(out, dict) else [],
            "final_report": out.get("final_report", "") if isinstance(out, dict) else "",
            "events": out.get("events", []) if isinstance(out, dict) else [],
            "done": bool(out.get("done")) if isinstance(out, dict) else False,
        }
        duration = round(time.time() - start_time, 3)
        logger.info(f"Ejecucion completada en {duration}s para thread_id={payload.thread_id}")
        return JSONResponse(snapshot)
    except Exception as e:
        logger.error(f"Error en /api/run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stream")
def stream(
    thread_id: str = Query(default="ddl-demo-1", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN),
    task_id: str = Query(default="DDL-2026-001", min_length=1, max_length=64),
):
    """
    Endpoint de Streaming NDJSON:
    Permite al frontend recibir actualizaciones parciales del grafo de agentes.
    """
    logger.info(f"Iniciando stream para thread_id={thread_id} task_id={task_id}")
    graph = get_graph()
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}

    def gen():
        try:
            for event in graph.stream({"task_id": task_id, "events": []}, config=cfg, stream_mode="values"):
                values = event if isinstance(event, dict) else {}

                snapshot = {
                    "task_id": values.get("task_id", ""),
                    "task": values.get("task", {}) or {},
                    "worker_results": values.get("worker_results", []) or [],
                    "conflicts": values.get("conflicts", []) or [],
                    "final_report": values.get("final_report", "") or "",
                    "events": values.get("events", []) or [],
                    "done": bool(values.get("done", False)),
                }

                payload_out = {"type": "snapshot", "snapshot": snapshot}
                yield (json.dumps(payload_out, ensure_ascii=False) + "\n").encode("utf-8")

            yield (json.dumps({"type": "final", "ok": True}) + "\n").encode("utf-8")
        except Exception as e:
            logger.error(f"Error en streaming para {thread_id}: {e}")
            yield (json.dumps({"type": "error", "detail": str(e)}) + "\n").encode("utf-8")
        finally:
            logger.info(f"Stream finalizado/cancelado para thread_id={thread_id}")

    return StreamingResponse(gen(), media_type="application/x-ndjson")
