import json
import logging
import time
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .graph import compile_graph

# Configuración de Logging Estructurado
logging.basicConfig(
    level=logging.INFO,
    format='{"ts": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "msg": "%(message)s"}',
)
logger = logging.getLogger("api")

logger = logging.getLogger("api")

app = FastAPI(title="Caso 09 – RR.HH. Screening + Agenda")

# Rutas robustas (CI/local/Docker):
# backend/src/api.py -> parents[1] = backend/
BACKEND_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = BACKEND_ROOT / "web"

# Solo montar estáticos si existe el directorio
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@lru_cache(maxsize=1)
def get_graph():
    """Compila el grafo SOLO cuando se necesita (evita romper pytest/CI al importar)."""
    return compile_graph()


@app.get("/health")
def health():
    """Liveness check."""
    return {"status": "ok", "ts": int(time.time())}


@app.get("/ready")
def ready():
    """Readiness check: verifica si el grafo compila y archivos existen."""
    try:
        _ = get_graph()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/healthz")
def healthz():
    # Mantengo compatible con el original
    return health()


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
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
    logger.info(f"Iniciando ejecución para thread_id: {payload.thread_id}")
    start_time = time.time()
    try:
        graph = get_graph()
        cfg = {"configurable": {"thread_id": payload.thread_id}, "recursion_limit": 50}
        out = graph.invoke({"events": []}, config=cfg)

        snapshot = {
            "job": (out.get("job") or {}) if isinstance(out, dict) else {},
            "scored": (out.get("scored") or []) if isinstance(out, dict) else [],
            "shortlist": (out.get("shortlist") or []) if isinstance(out, dict) else [],
            "scheduled": (out.get("scheduled") or []) if isinstance(out, dict) else [],
            "events": (out.get("events") or []) if isinstance(out, dict) else [],
            "done": bool(out.get("done")) if isinstance(out, dict) else False,
        }
        duration = round(time.time() - start_time, 3)
        logger.info(f"Ejecución completada en {duration}s para thread_id: {payload.thread_id}")
        return JSONResponse(snapshot)
    except Exception as e:
        logger.error(f"Error en /api/run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stream")
def stream(thread_id: str = "rrhh-demo-1"):
    """Streaming NDJSON para ver el flujo en tiempo real con soporte de cancelación."""
    logger.info(f"Iniciando stream para thread_id: {thread_id}")
    graph = get_graph()
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}

    def gen():
        try:
            for event in graph.stream({"events": []}, config=cfg):
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
        except Exception as e:
            logger.error(f"Error en streaming para {thread_id}: {e}")
            yield (json.dumps({"type": "error", "detail": str(e)}) + "\n").encode("utf-8")
        finally:
            logger.info(f"Stream finalizado/cancelado para thread_id: {thread_id}")

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
