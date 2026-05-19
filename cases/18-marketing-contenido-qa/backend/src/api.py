import json
import logging
import os
import time
import uuid
from contextvars import ContextVar
from functools import lru_cache
from time import monotonic

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .auth import auth_middleware, protected_path
from .graph import compile_graph
from .settings import web_dir as get_web_dir

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

app = FastAPI(title="Caso 18 - Marketing Contenido QA")
app.state.rate_limit_buckets = {}

_WEB_DIR = get_web_dir()
if _WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(_WEB_DIR), html=True), name="web")


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


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = _WEB_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>UI no disponible</h1>", status_code=404)
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/health")
def health():
    return {
        "status": "ok",
        "ts": int(time.time()),
        "mode": "LIVE" if os.getenv("OPENAI_API_KEY", "").strip() else "DEMO",
    }


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


class MarketingIn(BaseModel):
    thread_id: str = Field(default="mkt-demo-1", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)
    brief_id: str = Field(default="BR-001", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)


def _build_initial_state(brief_id: str) -> dict:
    return {
        "brief_id": brief_id,
        "brief": {},
        "borrador": "",
        "estilo": {},
        "hechos": {},
        "seo": {},
        "iter_estilo": 0,
        "iter_hechos": 0,
        "alucinaciones_retiradas_total": 0,
        "hechos_inyectados_total": 0,
        "score_global": 0,
        "riesgo": "",
        "decision_editor": "",
        "contenido_final": "",
        "diff": {},
        "metricas": {},
        "resumen": "",
        "events": [],
        "done": False,
    }


def _build_snapshot(out: dict, brief_id: str) -> dict:
    return {
        "brief_id": out.get("brief_id", brief_id),
        "brief": out.get("brief", {}),
        "borrador": out.get("borrador", ""),
        "estilo": out.get("estilo", {}),
        "hechos": out.get("hechos", {}),
        "seo": out.get("seo", {}),
        "iter_estilo": out.get("iter_estilo", 0),
        "iter_hechos": out.get("iter_hechos", 0),
        "score_global": out.get("score_global", 0),
        "riesgo": out.get("riesgo", ""),
        "decision_editor": out.get("decision_editor", ""),
        "contenido_final": out.get("contenido_final", ""),
        "diff": out.get("diff", {}),
        "metricas": out.get("metricas", {}),
        "resumen": out.get("resumen", ""),
        "events": out.get("events", []),
        "done": bool(out.get("done", False)),
    }


@app.post("/api/run")
def run(payload: MarketingIn):
    logger.info(f"Iniciando marketing: thread_id={payload.thread_id} brief_id={payload.brief_id}")
    start_time = time.time()
    try:
        graph = get_graph()
        cfg = {"configurable": {"thread_id": payload.thread_id}, "recursion_limit": 50}
        out = graph.invoke(_build_initial_state(payload.brief_id), config=cfg)
        snapshot = _build_snapshot(out if isinstance(out, dict) else {}, payload.brief_id)
        duration = round(time.time() - start_time, 3)
        logger.info(
            f"Marketing completado en {duration}s: brief={snapshot.get('brief',{}).get('id')} "
            f"score={snapshot.get('score_global')} riesgo={snapshot.get('riesgo')}"
        )
        return JSONResponse(snapshot)
    except Exception as exc:
        logger.exception("Unhandled error in /api/run")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.get("/api/stream")
def stream(
    thread_id: str = Query(default="mkt-demo-1", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN),
    brief_id: str = Query(default="BR-001", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN),
):
    logger.info(f"Iniciando stream: thread_id={thread_id} brief_id={brief_id}")
    graph = get_graph()
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}

    def gen():
        try:
            for event in graph.stream(
                _build_initial_state(brief_id), config=cfg, stream_mode="values"
            ):
                values = event if isinstance(event, dict) else {}
                snapshot = _build_snapshot(values, brief_id)
                yield (json.dumps({"type": "snapshot", "snapshot": snapshot}) + "\n").encode("utf-8")
            yield (json.dumps({"type": "final", "ok": True}) + "\n").encode("utf-8")
        except Exception as e:
            logger.error(f"Error en streaming para {thread_id}: {e}")
            yield (json.dumps({"type": "error", "detail": str(e)}) + "\n").encode("utf-8")
        finally:
            logger.info(f"Stream finalizado para thread_id={thread_id}")

    return StreamingResponse(gen(), media_type="application/x-ndjson")
