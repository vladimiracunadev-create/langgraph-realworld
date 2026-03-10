from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import asyncio
from .graph import graph
from .settings import settings

app = FastAPI(title="Case 13: BI Data Analyst")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos del frontend
app.mount("/web", StaticFiles(directory="/app/web", html=True), name="web")

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    question = data.get("question", "")
    
    async def event_generator():
        inputs = {"question": question}
        # stream_mode="values" para obtener el estado completo en cada paso
        async for output in graph.astream(inputs, stream_mode="values"):
            yield f"data: {json.dumps(output)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/")
async def root():
    return {"message": "Case 13: BI Data Analyst API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
