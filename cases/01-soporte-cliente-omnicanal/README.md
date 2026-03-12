# Caso 01: Soporte cliente omnicanal

Caso LangGraph para triage de tickets de soporte. Recibe un ticket, detecta intencion, calcula prioridad, enruta el caso, propone acciones y redacta una respuesta final para el cliente.

## Estado

- Backend FastAPI operativo
- LangGraph con estado tipado y streaming NDJSON
- Modo DEMO automatico
- Modo LIVE si existe configuracion usable de OpenAI
- UI local en `backend/web/index.html`

## Flujo LangGraph

- `load_ticket`
- `classify_intent`
- `prioritize_case`
- `route_case`
- `prepare_actions`
- `draft_response`
- `finalize_case`

## Ejecutar en local

```bash
cd cases/01-soporte-cliente-omnicanal/backend
uvicorn src.api:app --reload --port 8001
```

Abrir:

- API: `http://localhost:8001`
- UI: `http://localhost:8001/web/`

## Ejecutar con Docker

```bash
cd cases/01-soporte-cliente-omnicanal
docker compose -f backend/compose.yml up --build
```

## DEMO y LIVE

- `DEMO`: sin `OPENAI_API_KEY`, el caso funciona con reglas locales y conocimiento en JSON.
- `LIVE`: con `OPENAI_API_KEY` y `USE_LLM=true`, la clasificacion y la redaccion intentan usar LLM. Si falla, el caso degrada a DEMO sin romperse.

## Endpoints

- `GET /health`
- `GET /ready`
- `POST /api/run`
- `GET /api/stream`

## Datos demo

- `data/tickets.json`
- `data/kb_articles.json`
