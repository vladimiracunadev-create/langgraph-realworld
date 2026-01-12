import json
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .graph import compile_graph

app = FastAPI(title="Caso 09 – RR.HH. Screening + Agenda")

# Rutas robustas (CI/local/Docker):
# backend/src/api.py -> parents[1] = backend/
BACKEND_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = BACKEND_ROOT / "web"

# Solo montar estáticos si existe el directorio (en tests/CI igual existe, pero robustez extra)
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

GRAPH = compile_graph()


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        # En CI/test no siempre se usa /, pero si alguien lo llama, entrega mensaje claro
        return HTMLResponse(
            "<h1>UI no disponible</h1><p>Falta backend/web/index.html</p>",
            status_code=404,
        )
    return index_path.read_text(encoding="utf-8")


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
    """Streaming NDJSON para ver el flujo en tiempo real."""
    cfg = {"configurable": {"thread_id": thread_id}}

    def gen():
        for event in GRAPH.stream({"events": []}, config=cfg):
            values = event if isinstance(event, dict) else {}

            snapshot = {
                "job": values.get("job", {}) or {},
                "scored": values.get("scored", []) or [],
                "shortlist": values.get("shortlist", []) or [],
                "scheduled": values.get("scheduled", []) or [],
                "events": values.get("events", []) or [],
                "done": bool(values.get("done", False)),
            }

            payload_out = {"type": "snapshot", "snapshot": snapshot}
            yield (json.dumps(payload_out) + "\n").encode("utf-8")

        yield (json.dumps({"type": "final", "ok": True}) + "\n").encode("utf-8")

    return StreamingResponse(gen(), media_type="application/x-ndjson")


# ----------------------------
# STUB (para volverlo REAL)
# ----------------------------

@app.post("/api/cv/upload")
async def upload_cv(file: UploadFile = File(...)):
    """Subir un CV (stub)."""
    _ = file
    detail = "Stub: implementar almacenamiento + parsing en src/integrations.py"
    raise HTTPException(status_code=501, detail=detail)
