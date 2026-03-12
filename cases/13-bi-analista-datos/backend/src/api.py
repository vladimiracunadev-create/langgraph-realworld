import json
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .graph import EXAMPLE_QUESTIONS, IS_DEMO_MODE, graph
from .settings import settings

app = FastAPI(title="Case 13: BI Data Analyst")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.web_dir.exists():
    app.mount("/web", StaticFiles(directory=str(settings.web_dir), html=True), name="web")


def app_metadata() -> dict[str, Any]:
    return {
        "mode": "DEMO" if IS_DEMO_MODE else "LIVE",
        "database_path": str(settings.database_path),
        "web_dir": str(settings.web_dir),
        "examples": EXAMPLE_QUESTIONS,
    }


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
async def chat(request: Request):
    data = await request.json()
    question = (data.get("question") or "").strip()
    if not question:
        return JSONResponse(status_code=400, content={"detail": "Question is required."})

    async def event_generator():
        inputs = {"question": question}
        async for output in graph.astream(inputs, stream_mode="values"):
            payload = {**output, "mode": "DEMO" if IS_DEMO_MODE else "LIVE"}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
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
