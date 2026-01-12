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


@app.post("/api/run")
def run(payload: RunIn):
    """Ejecuta el flujo y devuelve un snapshot final (sin streaming)."""
    cfg = {"configurable": {"thread_id": payload.thread_id}}
    out = GRAPH.invoke({"events": []}, config=cfg)
    snapshot = {
        "job": (out.get("job") or {}) if isinstance(out, dict) else {},
        "scored": (out.get("scored") or []) if isinstance(out, dict) else [],
        "shortlist": (out.get("shortlist") or []) if isinstance(out, dict) else [],
        "scheduled": (out.get("scheduled") or []) if isinstance(out, dict) else [],
        "events": (out.get("events") or []) if isinstance(out, dict) else [],
        "done": bool(out.get("done")) if isinstance(out, dict) else False,
    }
    return JSONResponse(snapshot)


@app.get("/api/stream")
def stream(thread_id: str = "rrhh-demo-1"):
    """Streaming NDJSON para ver el flujo en tiempo real.

    El frontend (web/index.html) consume este endpoint y va pintando eventos.
    """
    cfg = {"configurable": {"thread_id": thread_id}}

    def gen():
        # En LangGraph, stream() emite estados parciales.
        for event in GRAPH.stream({"events": []}, config=cfg):
            if isinstance(event, dict):
                values = event
            else:
                values = {}

            snapshot = {
                "job": values.get("job", {}) or {},
                "scored": values.get("scored", []) or [],
                "shortlist": values.get("shortlist", []) or [],
                "scheduled": values.get("scheduled", []) or [],
                "events": values.get("events", []) or [],
                "done": bool(values.get("done", False)),
            }

            payload = {"type": "snapshot", "snapshot": snapshot}
            yield (json.dumps(payload) + "\n").encode("utf-8")

        yield (json.dumps({"type": "final", "ok": True}) + "\n").encode("utf-8")

    return StreamingResponse(gen(), media_type="application/x-ndjson")


# ----------------------------
# STUBS (para que lo vuelvas REAL)
# ----------------------------
# Estos endpoints NO resuelven el flujo real por sí solos (tú lo harás),
# pero te dejan el lugar exacto y la librería lista (python-multipart) para empezar.


@app.post("/api/cv/upload")
async def upload_cv(file: UploadFile = File(...)):
    """Subir un CV (stub).
    Idea real:
    - Guardar en disco/S3
    - parse_resume_to_text(ruta)
    - extract_candidate_signals(texto)
    - upsert_candidate_in_db(...)
    """
    detail = "Stub: implementar almacenamiento + parsing en src/integrations.py"
    raise HTTPException(status_code=501, detail=detail)
