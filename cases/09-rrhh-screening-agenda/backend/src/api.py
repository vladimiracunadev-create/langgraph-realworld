import json
from typing import Any, Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .graph import compile_graph

app = FastAPI(title="Caso 09 – RR.HH. Screening + Agenda")
app.mount("/static", StaticFiles(directory="web"), name="static")

GRAPH = compile_graph()


@app.get("/", response_class=HTMLResponse)
def index():
    with open("web/index.html", "r", encoding="utf-8") as f:
        return f.read()


class RunIn(BaseModel):
    thread_id: str = "rrhh-demo-1"


@app.post("/api/run/stream")
async def run_stream(payload: RunIn):
    config = {"configurable": {"thread_id": payload.thread_id}}

    async def gen():
        sent_events = [0]  # mutable counter

        async for mode, chunk in GRAPH.astream(
            {},
            config=config,
            stream_mode=["updates", "values"],
        ):
            if mode == "updates":
                yield (json.dumps({"type": "update", "data": chunk}) + "\n").encode("utf-8")

            if mode == "values":
                values: Dict[str, Any] = chunk
                events = values.get("events") or []
                if len(events) > sent_events[0]:
                    for ev in events[sent_events[0]:]:
                        yield (json.dumps({"type": "event", "event": ev}) + "\n").encode("utf-8")
                    sent_events[0] = len(events)

                snapshot = {
                    "cursor": values.get("cursor", 0),
                    "total": len(values.get("candidates", []) or []),
                    "scored": values.get("scored", []) or [],
                    "shortlist": values.get("shortlist", []) or [],
                    "scheduled": values.get("scheduled", []) or [],
                    "done": bool(values.get("done", False)),
                    "job": values.get("job", {}) or {},
                }
                yield (json.dumps({"type": "snapshot", "snapshot": snapshot}) + "\n").encode("utf-8")

        yield (json.dumps({"type": "final", "ok": True}) + "\n").encode("utf-8")

    return StreamingResponse(gen(), media_type="application/x-ndjson")


@app.get("/api/thread/{thread_id}/state")
def thread_state(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    snap = GRAPH.get_state(config)
    values = dict(getattr(snap, "values", {}) or {})
    return JSONResponse({
        "thread_id": thread_id,
        "next": list(getattr(snap, "next", ())),
        "values": values,
        "metadata": getattr(snap, "metadata", None),
        "created_at": getattr(snap, "created_at", None),
    })

# -----------------------------
# Endpoints "reales" (stubs)
# -----------------------------
# Estos endpoints NO resuelven el flujo real por sí solos (tú lo harás),
# pero te dejan el lugar exacto y la librería lista (python-multipart) para empezar.

from fastapi import UploadFile, File, HTTPException

@app.post("/api/cv/upload")
async def upload_cv(file: UploadFile = File(...)):
    """Subir un CV (stub).
    Idea real:
    - Guardar en disco/S3
    - parse_resume_to_text(ruta)
    - extract_candidate_signals(texto)
    - upsert_candidate_in_db(...)
    """
    raise HTTPException(status_code=501, detail="Stub: implementar almacenamiento + parsing en src/integrations.py")

