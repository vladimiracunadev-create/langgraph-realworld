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

app = FastAPI(title="Caso 11 - Tutor Adaptativo")
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


class TutorIn(BaseModel):
    thread_id: str = Field(default="tutor-demo-1", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)
    student_id: str = Field(default="STU-001", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)


def _build_initial_state(student_id: str) -> dict:
    return {
        "student_id": student_id,
        "student": {},
        "policy": {},
        "diagnostico_aplicado": False,
        "habilidad": 0.0,
        "habilidad_inicial": 0.0,
        "max_items": 0,
        "items_disponibles": [],
        "items_servidos": [],
        "current_item": {},
        "evaluacion_actual": {},
        "evaluaciones": [],
        "conceptos_dominados": [],
        "conceptos_a_remediar": [],
        "errores_consecutivos": 0,
        "ajuste_ultimo": "",
        "perfil_final": {},
        "reporte": "",
        "events": [],
        "done": False,
    }


def _build_snapshot(out: dict, student_id: str) -> dict:
    student = out.get("student", {}) or {}
    return {
        "student_id": out.get("student_id", student_id),
        "student": {
            "id": student.get("id"),
            "nombre": student.get("nombre"),
            "curso": student.get("curso"),
            "dominio": student.get("dominio"),
            "objetivo_sesion": student.get("objetivo_sesion"),
            "preferencia_formato": student.get("preferencia_formato"),
        },
        "diagnostico_aplicado": bool(out.get("diagnostico_aplicado", False)),
        "habilidad": out.get("habilidad", 0.0),
        "habilidad_inicial": out.get("habilidad_inicial", 0.0),
        "max_items": out.get("max_items", 0),
        "items_servidos": out.get("items_servidos", []),
        "current_item": out.get("current_item", {}),
        "evaluacion_actual": out.get("evaluacion_actual", {}),
        "evaluaciones": out.get("evaluaciones", []),
        "conceptos_dominados": out.get("conceptos_dominados", []),
        "conceptos_a_remediar": out.get("conceptos_a_remediar", []),
        "ajuste_ultimo": out.get("ajuste_ultimo", ""),
        "perfil_final": out.get("perfil_final", {}),
        "reporte": out.get("reporte", ""),
        "events": out.get("events", []),
        "done": bool(out.get("done", False)),
    }


@app.post("/api/run")
def run(payload: TutorIn):
    logger.info(f"Iniciando tutoría: thread_id={payload.thread_id} student_id={payload.student_id}")
    start_time = time.time()
    try:
        graph = get_graph()
        cfg = {"configurable": {"thread_id": payload.thread_id}, "recursion_limit": 80}
        out = graph.invoke(_build_initial_state(payload.student_id), config=cfg)
        snapshot = _build_snapshot(out if isinstance(out, dict) else {}, payload.student_id)
        duration = round(time.time() - start_time, 3)
        logger.info(
            f"Sesión completada en {duration}s: items={len(snapshot.get('evaluaciones', []))} "
            f"promocion={snapshot.get('perfil_final', {}).get('promocion')}"
        )
        return JSONResponse(snapshot)
    except Exception as e:
        logger.error(f"Error en /api/run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stream")
def stream(
    thread_id: str = Query(default="tutor-demo-1", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN),
    student_id: str = Query(default="STU-001", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN),
):
    logger.info(f"Iniciando stream: thread_id={thread_id} student_id={student_id}")
    graph = get_graph()
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 80}

    def gen():
        try:
            for event in graph.stream(
                _build_initial_state(student_id), config=cfg, stream_mode="values"
            ):
                values = event if isinstance(event, dict) else {}
                snapshot = _build_snapshot(values, student_id)
                yield (json.dumps({"type": "snapshot", "snapshot": snapshot}) + "\n").encode("utf-8")
            yield (json.dumps({"type": "final", "ok": True}) + "\n").encode("utf-8")
        except Exception as e:
            logger.error(f"Error en streaming para {thread_id}: {e}")
            yield (json.dumps({"type": "error", "detail": str(e)}) + "\n").encode("utf-8")
        finally:
            logger.info(f"Stream finalizado para thread_id={thread_id}")

    return StreamingResponse(gen(), media_type="application/x-ndjson")
