import json
import os
from collections import deque
from hmac import compare_digest
from time import monotonic
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .graph import EXAMPLE_QUESTIONS, IS_DEMO_MODE, graph
from .settings import settings

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


def demo_auth_token() -> str:
    return os.getenv("DEMO_AUTH_TOKEN", "").strip()


def rate_limit_rpm() -> int:
    raw = os.getenv("RATE_LIMIT_RPM", "0").strip()
    try:
        return max(int(raw), 0)
    except ValueError:
        return 0


def trust_proxy_headers() -> bool:
    return os.getenv("TRUST_PROXY_HEADERS", "false").strip().lower() in {"1", "true", "yes", "on"}


def protected_path(path: str) -> bool:
    return path == "/chat"


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


@app.post("/chat")
async def chat(payload: ChatRequest):
    question = payload.question.strip()

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
