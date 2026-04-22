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

app = FastAPI(title="Caso 04 - SOC Triage de Alertas")
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
    return compile_graph()


@app.get("/health")
def health():
    return {"status": "ok", "ts": int(time.time())}


@app.get("/healthz")
def healthz():
    return health()


@app.get("/ready")
def ready():
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


class TriageIn(BaseModel):
    thread_id: str = Field(default="soc-demo-1", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)
    alert_id: str = Field(default="ALT-001", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)


def _build_initial_state(alert_id: str) -> dict:
    return {
        "alert_id": alert_id,
        "alert": {},
        "ioc_enrichment": {},
        "mitre_techniques": [],
        "siem_context": {},
        "risk_score": 0,
        "risk_level": "",
        "triage_decision": "",
        "investigation_result": "",
        "analyst_assignment": {},
        "close_record": {},
        "triage_report": "",
        "events": [],
        "done": False,
    }


def _build_snapshot(out: dict, alert_id: str) -> dict:
    return {
        "alert_id": out.get("alert_id", alert_id),
        "alert_title": out.get("alert", {}).get("title", ""),
        "risk_score": out.get("risk_score", 0),
        "risk_level": out.get("risk_level", ""),
        "triage_decision": out.get("triage_decision", ""),
        "investigation_result": out.get("investigation_result", ""),
        "mitre_techniques": out.get("mitre_techniques", []),
        "analyst_assignment": out.get("analyst_assignment", {}),
        "close_record": out.get("close_record", {}),
        "triage_report": out.get("triage_report", ""),
        "events": out.get("events", []),
        "done": bool(out.get("done", False)),
    }


@app.post("/api/run")
def run(payload: TriageIn):
    """Ejecuta el flujo completo de SOC triage y devuelve el snapshot final."""
    logger.info(f"Iniciando triage: thread_id={payload.thread_id} alert_id={payload.alert_id}")
    start_time = time.time()
    try:
        graph = get_graph()
        cfg = {"configurable": {"thread_id": payload.thread_id}, "recursion_limit": 50}
        out = graph.invoke(_build_initial_state(payload.alert_id), config=cfg)

        snapshot = _build_snapshot(
            out if isinstance(out, dict) else {},
            payload.alert_id,
        )
        duration = round(time.time() - start_time, 3)
        logger.info(f"Triage completado en {duration}s: thread_id={payload.thread_id} "
                    f"risk={snapshot['risk_score']} decision={snapshot['triage_decision']}")
        return JSONResponse(snapshot)
    except Exception as e:
        logger.error(f"Error en /api/run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stream")
def stream(
    thread_id: str = Query(default="soc-demo-1", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN),
    alert_id: str = Query(default="ALT-001", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN),
):
    """
    Streaming NDJSON: emite un snapshot del estado del agente tras cada nodo.
    Permite al frontend mostrar el progreso del triage en tiempo real.
    """
    logger.info(f"Iniciando stream: thread_id={thread_id} alert_id={alert_id}")
    graph = get_graph()
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}

    def gen():
        try:
            for event in graph.stream(
                _build_initial_state(alert_id), config=cfg, stream_mode="values"
            ):
                values = event if isinstance(event, dict) else {}
                snapshot = _build_snapshot(values, alert_id)
                yield (json.dumps({"type": "snapshot", "snapshot": snapshot}) + "\n").encode("utf-8")

            yield (json.dumps({"type": "final", "ok": True}) + "\n").encode("utf-8")
        except Exception as e:
            logger.error(f"Error en streaming para {thread_id}: {e}")
            yield (json.dumps({"type": "error", "detail": str(e)}) + "\n").encode("utf-8")
        finally:
            logger.info(f"Stream finalizado para thread_id={thread_id}")

    return StreamingResponse(gen(), media_type="application/x-ndjson")
