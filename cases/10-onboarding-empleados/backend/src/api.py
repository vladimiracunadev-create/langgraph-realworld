import json
import logging
import time
import uuid
from contextvars import ContextVar
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .graph import compile_graph

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

app = FastAPI(title="Caso 10 – Onboarding de Empleados")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = BACKEND_ROOT / "web"
SHARED_ASSETS_DIR = BACKEND_ROOT.parents[2] / "assets"

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
if SHARED_ASSETS_DIR.exists():
    app.mount("/shared-assets", StaticFiles(directory=str(SHARED_ASSETS_DIR)), name="shared-assets")


@app.middleware("http")
async def add_trace_id_middleware(request, call_next):
    id_ = str(uuid.uuid4())
    token = trace_id_var.set(id_)
    try:
        response = await call_next(request)
        response.headers["X-Trace-ID"] = id_
        return response
    finally:
        trace_id_var.reset(token)


@lru_cache(maxsize=1)
def get_graph():
    return compile_graph()


@app.get("/health")
def health():
    return {"status": "ok", "ts": int(time.time())}


@app.get("/ready")
def ready():
    try:
        _ = get_graph()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/healthz")
def healthz():
    return health()


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse(
            "<h1>UI no disponible</h1><p>Falta backend/web/index.html</p>",
            status_code=404,
        )
    html = index_path.read_text(encoding="utf-8")
    html = html.replace(
        "<body>",
        "<body data-api-config-cases=\"10\" data-api-config-title=\"APIs del Caso 10\">",
        1,
    )
    html = html.replace(
        "</body>",
        "  <script src=\"/shared-assets/api-config.js\"></script>\n</body>",
        1,
    )
    return html


class RunIn(BaseModel):
    thread_id: str = "onboarding-demo-1"
    employee_id: str = "EMP-2026-001"


@app.post("/api/run")
def run(payload: RunIn):
    """Ejecuta el flujo completo de onboarding y devuelve snapshot final."""
    logger.info(f"Iniciando onboarding para thread_id: {payload.thread_id}")
    start_time = time.time()
    try:
        graph = get_graph()
        cfg = {
            "configurable": {"thread_id": payload.thread_id},
            "recursion_limit": 30,
        }
        out = graph.invoke({"events": []}, config=cfg)

        snapshot = {
            "employee": (out.get("employee") or {}) if isinstance(out, dict) else {},
            "role_type": (out.get("role_type") or "") if isinstance(out, dict) else "",
            "tools_provisioned": (out.get("tools_provisioned") or []) if isinstance(out, dict) else [],
            "accounts": (out.get("accounts") or []) if isinstance(out, dict) else [],
            "permissions": (out.get("permissions") or []) if isinstance(out, dict) else [],
            "checklist": (out.get("checklist") or []) if isinstance(out, dict) else [],
            "notifications": (out.get("notifications") or []) if isinstance(out, dict) else [],
            "events": (out.get("events") or []) if isinstance(out, dict) else [],
            "done": bool(out.get("done")) if isinstance(out, dict) else False,
        }
        duration = round(time.time() - start_time, 3)
        logger.info(f"Onboarding completado en {duration}s para {payload.thread_id}")
        return JSONResponse(snapshot)
    except Exception as e:
        logger.error(f"Error en /api/run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stream")
def stream(thread_id: str = "onboarding-demo-1"):
    """
    Streaming NDJSON en tiempo real del flujo de onboarding.
    Permite a la UI mostrar cada fase a medida que se completa.
    """
    logger.info(f"Iniciando stream para thread_id: {thread_id}")
    graph = get_graph()
    cfg = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 30,
    }

    def gen():
        try:
            for event in graph.stream({"events": []}, config=cfg, stream_mode="values"):
                values = event if isinstance(event, dict) else {}
                snapshot = {
                    "employee": values.get("employee") or {},
                    "role_type": values.get("role_type") or "",
                    "tools_provisioned": values.get("tools_provisioned") or [],
                    "accounts": values.get("accounts") or [],
                    "permissions": values.get("permissions") or [],
                    "checklist": values.get("checklist") or [],
                    "notifications": values.get("notifications") or [],
                    "events": values.get("events") or [],
                    "done": bool(values.get("done", False)),
                }
                payload_out = {"type": "snapshot", "snapshot": snapshot}
                yield (json.dumps(payload_out) + "\n").encode("utf-8")

            yield (json.dumps({"type": "final", "ok": True}) + "\n").encode("utf-8")
        except Exception as e:
            logger.error(f"Error en streaming para {thread_id}: {e}")
            yield (json.dumps({"type": "error", "detail": str(e)}) + "\n").encode("utf-8")
        finally:
            logger.info(f"Stream finalizado para thread_id: {thread_id}")

    return StreamingResponse(gen(), media_type="application/x-ndjson")
