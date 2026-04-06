# Caso 02: Mesa de Ayuda TI / SRE Helpdesk

> [!IMPORTANT]
> **Estado**: Operational | **Version**: 3.8.0 | **Referencia**: FastAPI + LangGraph + SRE Terminal

Sistema de respuesta autonoma para Helpdesk corporativo, MLOps e incidentes SRE. Combina enriquecimiento de contexto desde CMDB mock, clasificacion guiada por LangGraph, HITL simulado y ejecucion esteril de runbooks.

## Flujo principal

1. `receive_ticket`
2. `enrich_ticket`
3. `classify_issue`
4. `select_runbook`
5. `request_approval`
6. `execute_runbook`
7. `validate_resolution`
8. `draft_response`

## Controles y compatibilidad

- Fallback DEMO por defecto cuando no existe `OPENAI_API_KEY`.
- Bypass temprano para tickets `unsupported`.
- Validacion de `thread_id` y payloads en la API.
- `DEMO_AUTH_TOKEN` y `RATE_LIMIT_RPM` opcionales para exposicion externa controlada.
- Suite propia de tests para API, auth opcional, rate limiting y flujo LangGraph.

## Como ejecutar

```bash
cd backend
uvicorn src.api:app --reload --port 8002
```

UI del caso: [http://localhost:8002/web/](http://localhost:8002/web/)
