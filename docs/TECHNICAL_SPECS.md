# Especificaciones Tecnicas

> [!NOTE]
> **Version**: 3.8.0 | **Estado**: Industrial | **Audiencia**: Senior Backend Engineers, SREs

## Stack Core

| Capa | Tecnologia principal | Proposito |
|---|---|---|
| API Backend | `FastAPI` (Python 3.11) | Endpoints REST, streaming y health checks |
| Servidor App | `Uvicorn` | Runtime ASGI liviano |
| Orquestacion AI | `LangGraph` + `LangChain` | Grafos con estado, routing y checkpoints |
| Deployment | `Docker` y `Docker Compose` | Aislamiento y levantamiento paralelo |
| Frontend | HTML/CSS/JS | UIs ligeras y explorables |
| Calidad | `pytest`, `ruff`, `compileall` | Validacion rapida del monorepo |
| Seguridad CI | `CodeQL`, `detect-secrets`, `pip-audit` | Hardening de codigo, secretos y supply chain |

## Contratos tecnicos relevantes

- Estado tipado con `TypedDict` y merges controlados por caso.
- Endpoints `/health` y `/ready` como contrato operativo minimo.
- Stream NDJSON o SSE segun el caso para interfaces en tiempo real.
- Configuracion por `.env.example` con degradacion clara a modo DEMO.
- `case.yml` como contrato de arranque para Hub CLI, validado por allowlist.

## Guardrails aplicados

- IDs y payloads con validacion de longitud y patron.
- `hub.py` sin ejecucion arbitraria por shell.
- Caso 13 con SQL solo lectura, comentarios bloqueados y limite de filas.
- Casos operativos con `X-Demo-Token` y rate limiting opcionales para exposicion externa.
- Caso 02 con suite propia de API y flujo LangGraph para evitar regresiones silenciosas.

## Implicancias para DX

La seguridad no se integra como bloqueo ciego:

- PRs mantienen auditoria de dependencias en modo `soft`.
- Los nuevos guardrails de exposicion son opt-in.
- Los ejemplos pedagogicos siguen funcionando en DEMO aunque falten secretos reales.
- El quickstart local sigue siendo `docker compose up --build` o `uvicorn src.api:app`.
