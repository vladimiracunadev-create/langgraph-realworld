import json
import logging
import os
from collections import deque
from hmac import compare_digest
from time import monotonic
from typing import Dict

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .graph import compile_graph
from .integrations import _is_live
from .settings import backend_root, cors_allowed_origins, load_settings

load_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
SAFE_ID_PATTERN = r"^[A-Za-z0-9._:-]{1,64}$"

app = FastAPI(title="Caso 02 - Mesa de Ayuda TI")
app.state.rate_limit_buckets = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


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
async def enforce_demo_guards(request: Request, call_next):
    limit = rate_limit_rpm()
    response = None

    if protected_path(request.url.path):
        token = demo_auth_token()
        if token:
            provided = request.headers.get("x-demo-token", "").strip()
            if not compare_digest(provided, token):
                return JSONResponse(status_code=401, content={"detail": "Missing or invalid X-Demo-Token"})

        if limit > 0:
            now = monotonic()
            bucket = app.state.rate_limit_buckets.setdefault(client_identity(request), deque())
            while bucket and now - bucket[0] >= 60:
                bucket.popleft()
            if len(bucket) >= limit:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
            bucket.append(now)

    response = await call_next(request)
    if limit > 0 and protected_path(request.url.path):
        bucket = app.state.rate_limit_buckets.get(client_identity(request), deque())
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(limit - len(bucket), 0))
    return response

class RunRequest(BaseModel):
    ticket: str = Field(..., min_length=1, max_length=4000)
    thread_id: str = Field(default="demo-thread", min_length=1, max_length=64, pattern=SAFE_ID_PATTERN)

graph_app = compile_graph()

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "mode": "live" if _is_live() else "demo"}

@app.get("/ready")
def ready() -> Dict[str, str]:
    return {"ready": "yes", "case": "02"}

@app.post("/api/run")
async def run_ticket(req: RunRequest):
    """Ejecuta el grafo completo (útil para tests sincrónicos)."""
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
                # values contains exactly the TypedDict of the state
                # we just dump events diff
                yield f"{json.dumps(s)}\\n"
        except Exception as e:
            logger.error(f"Error en stream: {e}")
            yield f"{json.dumps({'error': str(e)})}\\n"
            
    return StreamingResponse(event_generator(), media_type="application/ndjson")

# Mount web
web_path = backend_root() / "web"
if web_path.exists():
    app.mount("/web", StaticFiles(directory=str(web_path), html=True), name="web")
