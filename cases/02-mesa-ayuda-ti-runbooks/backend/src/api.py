import json
import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .graph import compile_graph
from .integrations import _is_live
from .settings import load_settings, backend_root

load_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Caso 02 - Mesa de Ayuda TI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    ticket: str
    thread_id: str = "demo-thread"

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
async def stream_ticket(ticket: str, thread_id: str = "demo-thread"):
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
            yield f"{{'error': '{str(e)}'}}\\n"
            
    return StreamingResponse(event_generator(), media_type="application/ndjson")

# Mount web
web_path = backend_root() / "web"
if web_path.exists():
    app.mount("/web", StaticFiles(directory=str(web_path), html=True), name="web")
