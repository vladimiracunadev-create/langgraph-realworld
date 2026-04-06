import json
import logging
import os
import time
import uuid
from collections import deque
from contextvars import ContextVar
from functools import lru_cache
from hmac import compare_digest
from pathlib import Path
from time import monotonic

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

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
logging.getLogger().addFilter(TraceIdFilter())
logger = logging.getLogger("api")

app = FastAPI(title="Caso 10 - Onboarding de Empleados")
app.state.rate_limit_buckets = {}

BACKEND_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = BACKEND_ROOT / "web"
SHARED_ASSETS_DIR = BACKEND_ROOT.parents[2] / "assets"

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
if SHARED_ASSETS_DIR.exists():
    app.mount("/shared-assets", StaticFiles(directory=str(SHARED_ASSETS_DIR)), name="shared-assets")


def demo_auth_token() -> str:
    return os.getenv("DEMO_AUTH_TOKEN", "").strip()


def rate_limit_rpm() -> int:
    raw = os.getenv("RATE_LIMIT_RPM", "0").strip()
    try:
        return max(int(raw), 0)
    except ValueError:
        logger.warning("RATE_LIMIT_RPM invalido: %s", raw)
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
async def add_trace_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    ctx_token = trace_id_var.set(request_id)
    limit = rate_limit_rpm()
    try:
        if protected_path(request.url.path):
            expected_token = demo_auth_token()
            if expected_token:
                provided = request.headers.get("x-demo-token", "").strip()
                if not compare_digest(provided, expected_token):
                    response = JSONResponse(status_code=401, content={"detail": "Missing or invalid X-Demo-Token"})
                    response.headers["X-Trace-ID"] = request_id
                    return response

            if limit > 0:
                now = monotonic()
                bucket = app.state.rate_limit_buckets.setdefault(client_identity(request), deque())
                while bucket and now - bucket[0] >= 60:
                    bucket.popleft()
                if len(bucket) >= limit:
                    response = JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
                    response.headers["X-Trace-ID"] = request_id
                    response.headers["X-RateLimit-Limit"] = str(limit)
                    response.headers["X-RateLimit-Remaining"] = "0"
                    return response
                bucket.append(now)

        response = await call_next(request)
        response.headers["X-Trace-ID"] = request_id
        if limit > 0 and protected_path(request.url.path):
            bucket = app.state.rate_limit_buckets.get(client_identity(request), deque())
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(limit - len(bucket), 0))
        return response
    finally:
        trace_id_var.reset(ctx_token)


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
        '<body data-api-config-cases="10" data-api-config-title="APIs del Caso 10">',
        1,
    )
    html = html.replace(
        "</body>",
        '  <script src="/shared-assets/api-config.js"></script>\n</body>',
        1,
    )
    return html


class RunIn(BaseModel):
    thread_id: str = Field(default="onboarding-demo-1", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)
    employee_id: str = Field(default="EMP-2026-001", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)


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
def stream(
    thread_id: str = Query(default="onboarding-demo-1", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN),
):
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
