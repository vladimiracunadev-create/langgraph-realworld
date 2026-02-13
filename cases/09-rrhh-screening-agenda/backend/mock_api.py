import asyncio
import json
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

# Mapear archivos estáticos
WEB_DIR = Path(__file__).parent / "web"
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = WEB_DIR / "index.html"
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))

@app.post("/api/run/stream")
async def run_stream(request: Request):
    data = await request.json()
    thread_id = data.get("thread_id", "mock-thread")
    
    async def event_generator():
        # Datos de prueba
        candidates = [
            {"candidate_id": "C-001", "name": "Ana García", "score": 92, "must_hits": 5, "must_misses": 0, "nice_hits": 3, "status": "scored"},
            {"candidate_id": "C-002", "name": "Carlos Ruiz", "score": 78, "must_hits": 4, "must_misses": 1, "nice_hits": 2, "status": "scored"},
            {"candidate_id": "C-003", "name": "Elena Belmonte", "score": 45, "must_hits": 2, "must_misses": 3, "nice_hits": 1, "status": "scored"},
            {"candidate_id": "C-004", "name": "David Soria", "score": 88, "must_hits": 5, "must_misses": 0, "nice_hits": 4, "status": "scored"}
        ]
        
        job_info = {"title": "Senior AI Architect", "location": "Madrid (Remote)"}
        
        # Simular pasos del grafo
        yield json.dumps({"type": "info", "msg": f"Iniciando screening para thread: {thread_id}"}) + "\n"
        await asyncio.sleep(0.5)
        
        for i, c in enumerate(candidates):
            yield json.dumps({"type": "info", "msg": f"Evaluando candidato {c['name']}..."}) + "\n"
            await asyncio.sleep(1)
            
            # Mandar snapshot parcial
            snapshot = {
                "cursor": i + 1,
                "total": len(candidates),
                "job": job_info,
                "scored": candidates[:i+1],
                "shortlist": [x for x in candidates[:i+1] if x["score"] > 80]
            }
            yield json.dumps({"type": "snapshot", "snapshot": snapshot}) + "\n"
        
        yield json.dumps({"type": "info", "msg": "Screening completado. Generando agenda..."}) + "\n"
        await asyncio.sleep(1)
        
        final_snapshot = {
            "cursor": len(candidates),
            "total": len(candidates),
            "job": job_info,
            "scored": candidates,
            "shortlist": [x for x in candidates if x["score"] > 80],
            "scheduled": [x for x in candidates if x["score"] > 85]
        }
        yield json.dumps({"type": "snapshot", "snapshot": final_snapshot}) + "\n"
        yield json.dumps({"type": "final", "msg": "Proceso finalizado con éxito."}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    # uvicorn doesn't have a direct allow_reuse_address flag in .run, 
    # but it's enabled by default in mostuvicorn setups. 
    # If not, we use the low level config.
    uvicorn.run(app, host="0.0.0.0", port=8009)
