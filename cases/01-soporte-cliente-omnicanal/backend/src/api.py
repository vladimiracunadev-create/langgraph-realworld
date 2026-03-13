from __future__ import annotations

import json
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .graph import compile_graph
from .settings import data_dir, host, mode_label, port, web_dir

app = FastAPI(title="Caso 01 - Soporte cliente omnicanal")

WEB_DIR = web_dir()
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
SHARED_ASSETS_DIR = Path(__file__).resolve().parents[4] / "assets"
if SHARED_ASSETS_DIR.exists():
    app.mount("/shared-assets", StaticFiles(directory=str(SHARED_ASSETS_DIR)), name="shared-assets")


class RunIn(BaseModel):
    thread_id: str = Field(default="support-demo-01")
    ticket_id: str = Field(default="T-001")
    ticket: dict[str, Any] | None = None


@lru_cache(maxsize=1)
def get_graph():
    return compile_graph()


def metadata() -> dict[str, Any]:
    return {
        "mode": mode_label(),
        "port": port(),
        "data_dir": str(data_dir()),
        "web_dir": str(WEB_DIR),
    }


@app.get("/health")
def health():
    return {"status": "ok", "ts": int(time.time()), **metadata()}


@app.get("/healthz")
def healthz():
    return health()


@app.get("/ready")
def ready():
    if not data_dir().exists():
        raise HTTPException(status_code=503, detail="Data directory not found")
    if not WEB_DIR.exists():
        raise HTTPException(status_code=503, detail="Web directory not found")
    _ = get_graph()
    return {"status": "ready", **metadata()}


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>UI no disponible</h1>", status_code=404)
    html = index_path.read_text(encoding="utf-8")
    html = html.replace(
        "<body>",
        "<body data-api-config-cases=\"01\" data-api-config-title=\"APIs del Caso 01\">",
        1,
    )
    html = html.replace(
        "</body>",
        "  <script src=\"/shared-assets/api-config.js\"></script>\n</body>",
        1,
    )
    return html


@app.post("/api/run")
def run(payload: RunIn):
    graph = get_graph()
    cfg = {"configurable": {"thread_id": payload.thread_id}, "recursion_limit": 20}
    try:
        out = graph.invoke({"request": payload.model_dump(), "events": []}, config=cfg)
        snapshot = {
            "ticket": out.get("ticket") or {},
            "intent": out.get("intent") or "",
            "priority": out.get("priority") or "",
            "route": out.get("route") or {},
            "knowledge": out.get("knowledge") or {},
            "actions": out.get("actions") or [],
            "response": out.get("response") or "",
            "events": out.get("events") or [],
            "done": bool(out.get("done", False)),
            "mode": out.get("mode") or mode_label(),
        }
        return JSONResponse(snapshot)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/stream")
def stream(ticket_id: str = "T-001", thread_id: str = "support-demo-01"):
    graph = get_graph()
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}

    def gen():
        try:
            for state in graph.stream({"request": {"ticket_id": ticket_id}, "events": []}, config=cfg, stream_mode="values"):
                snapshot = {
                    "ticket": state.get("ticket") or {},
                    "intent": state.get("intent") or "",
                    "priority": state.get("priority") or "",
                    "route": state.get("route") or {},
                    "knowledge": state.get("knowledge") or {},
                    "actions": state.get("actions") or [],
                    "response": state.get("response") or "",
                    "events": state.get("events") or [],
                    "done": bool(state.get("done", False)),
                    "mode": state.get("mode") or mode_label(),
                }
                yield (json.dumps({"type": "snapshot", "snapshot": snapshot}, ensure_ascii=False) + "\n").encode("utf-8")
            yield (json.dumps({"type": "final", "ok": True}) + "\n").encode("utf-8")
        except Exception as exc:
            yield (json.dumps({"type": "error", "detail": str(exc)}) + "\n").encode("utf-8")

    return StreamingResponse(gen(), media_type="application/x-ndjson")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=host(), port=port())
