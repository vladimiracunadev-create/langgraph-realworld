# 🤖 Caso 09: RR.HH. Screening + Agenda (Industrial v3.4.0)

> [!IMPORTANT]
> **Estado**: Industrial | **Versión**: 3.4.0 | **Referencia**: Resiliencia y observabilidad

Caso de referencia para screening, shortlist, agenda y notificación con LangGraph.

## Qué demuestra

- flujo de negocio completo;
- streaming de progreso;
- trazabilidad con `trace_id`;
- degradación razonable frente a fallos de integración;
- API backend real con FastAPI.

## Implementación actual

- estado tipado con `TypedDict`;
- `MemorySaver` como checkpointer actual para demos y desarrollo local;
- endpoints `/health`, `/ready`, `/api/run` y `/api/stream`.

## Ejecución rápida

### Docker

```bash
docker compose up --build case09
```

### Local

```bash
cd cases/09-rrhh-screening-agenda/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.api:app --port 8009
```