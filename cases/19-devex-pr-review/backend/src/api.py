"""
api.py — FastAPI para el agente de revisión de PRs (Caso 19 - DevEx PR Review).

Endpoints:
  GET  /health    — Liveness check
  GET  /healthz   — Alias de /health
  GET  /ready     — Readiness check (verifica que el grafo compila)
  GET  /metrics   — Métricas de observabilidad
  POST /api/run   — Ejecuta la revisión completa y devuelve snapshot final
  GET  /api/stream — Streaming NDJSON con actualizaciones paso a paso
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

# ---------------------------------------------------------------------------
# Logging JSON con trace_id
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

_metrics: dict = {"requests": 0, "errors": 0, "latency_sum": 0.0, "start_time": time.time()}

app = FastAPI(title="Caso 19 - DevEx PR Review Agent")
app.state.rate_limit_buckets = {}


# ---------------------------------------------------------------------------
# Middleware de observabilidad + auth
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
# Graph (lazy init)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_graph():
    """Compila el grafo SOLO cuando se necesita (evita romper pytest/CI al importar)."""
    return compile_graph()


# ---------------------------------------------------------------------------
# Health & Metrics endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    """Liveness check."""
    return {"status": "ok", "ts": int(time.time())}


@app.get("/healthz")
def healthz():
    """Alias de /health."""
    return health()


@app.get("/ready")
def ready():
    """Readiness check: verifica que el grafo compila correctamente."""
    try:
        _ = get_graph()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/metrics")
def metrics():
    """Métricas básicas de observabilidad."""
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


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

class RunIn(BaseModel):
    thread_id: str = Field(
        default="pr-review-demo-1",
        min_length=1,
        max_length=64,
        pattern=SAFE_ID_PATTERN,
    )
    pr_id: str = Field(
        default="PR-001",
        min_length=1,
        max_length=64,
        pattern=SAFE_ID_PATTERN,
    )


@app.post("/api/run")
def run(payload: RunIn):
    """
    Ejecuta la revisión completa del PR y devuelve un snapshot final (sin streaming).

    Invoke el grafo con pr_id y thread_id, devuelve el estado final incluyendo:
    - all_findings: lista de findings de seguridad, calidad y tests
    - risk_level: nivel de riesgo ("high", "medium", "low")
    - decision: decisión de revisión
    - changelog: changelog generado
    - done: indicador de finalización
    """
    logger.info(f"Iniciando revision PR {payload.pr_id} para thread_id: {payload.thread_id}")
    start_time = time.time()
    try:
        graph = get_graph()
        cfg = {"configurable": {"thread_id": payload.thread_id}, "recursion_limit": 50}
        initial_state = {
            "pr_id": payload.pr_id,
            "events": [],
        }
        out = graph.invoke(initial_state, config=cfg)

        snapshot = {
            "pr_id": out.get("pr_id", payload.pr_id) if isinstance(out, dict) else payload.pr_id,
            "pr_data": (out.get("pr_data") or {}) if isinstance(out, dict) else {},
            "security_findings": (out.get("security_findings") or []) if isinstance(out, dict) else [],
            "quality_findings": (out.get("quality_findings") or []) if isinstance(out, dict) else [],
            "test_findings": (out.get("test_findings") or []) if isinstance(out, dict) else [],
            "all_findings": (out.get("all_findings") or []) if isinstance(out, dict) else [],
            "risk_level": out.get("risk_level", "low") if isinstance(out, dict) else "low",
            "decision": out.get("decision", "approve") if isinstance(out, dict) else "approve",
            "changelog": out.get("changelog", "") if isinstance(out, dict) else "",
            "events": (out.get("events") or []) if isinstance(out, dict) else [],
            "done": bool(out.get("done")) if isinstance(out, dict) else False,
        }
        duration = round(time.time() - start_time, 3)
        logger.info(
            f"Revision completada en {duration}s para PR {payload.pr_id}. "
            f"Decision: {snapshot['decision']}. Risk: {snapshot['risk_level']}"
        )
        return JSONResponse(snapshot)
    except Exception as exc:
        logger.exception("Unhandled error in /api/run")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.get("/api/stream")
def stream(
    thread_id: str = Query(
        default="pr-review-demo-1",
        min_length=1,
        max_length=64,
        pattern=SAFE_ID_PATTERN,
    ),
    pr_id: str = Query(default="PR-001", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN),
):
    """
    Endpoint de Streaming NDJSON:
    - Permite al frontend recibir actualizaciones parciales del grafo de agentes.
    - Útil para interfaces que muestran el progreso de la revisión paso a paso.
    - Soporta thread_id para persistencia de sesión por usuario.
    """
    logger.info(f"Iniciando stream para PR {pr_id}, thread_id: {thread_id}")
    graph = get_graph()
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}
    initial_state = {"pr_id": pr_id, "events": []}

    def gen():
        try:
            for event in graph.stream(initial_state, config=cfg, stream_mode="values"):
                values = event if isinstance(event, dict) else {}

                snapshot = {
                    "pr_id": values.get("pr_id", pr_id),
                    "security_findings": values.get("security_findings", []) or [],
                    "quality_findings": values.get("quality_findings", []) or [],
                    "test_findings": values.get("test_findings", []) or [],
                    "all_findings": values.get("all_findings", []) or [],
                    "risk_level": values.get("risk_level", ""),
                    "decision": values.get("decision", ""),
                    "changelog": values.get("changelog", ""),
                    "events": values.get("events", []) or [],
                    "done": bool(values.get("done", False)),
                }

                payload_out = {"type": "snapshot", "snapshot": snapshot}
                yield (json.dumps(payload_out) + "\n").encode("utf-8")

            yield (json.dumps({"type": "final", "ok": True}) + "\n").encode("utf-8")
        except Exception as e:
            logger.error(f"Error en streaming para {thread_id}: {e}")
            yield (json.dumps({"type": "error", "detail": str(e)}) + "\n").encode("utf-8")
        finally:
            logger.info(f"Stream finalizado/cancelado para thread_id: {thread_id}")

    return StreamingResponse(gen(), media_type="application/x-ndjson")
