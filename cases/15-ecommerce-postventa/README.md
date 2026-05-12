# Caso 15 — E-commerce Postventa

> **Estado**: `OPERATIVO` · **Versión repo**: 4.10.0 · **Puerto**: 8015

Agente de postventa para e-commerce que automatiza seguimiento de pedidos, devoluciones
y cambios de talla/color. Integra OMS, política de devoluciones e inventario, generando
etiquetas de retorno con trazabilidad SHA-256 cuando procede o derivando al equipo
humano cuando el caso supera la política automatizable.

## Objetivo de negocio

Los equipos de soporte postventa dedican hasta el 40% del tiempo a consultas repetitivas
sobre estado de pedidos y gestión de devoluciones. Este agente automatiza la
clasificación, verificación de elegibilidad y generación de documentos, liberando al
equipo para casos complejos que requieren juicio humano.

## Flujo LangGraph

```
recibir_solicitud → lookup_pedido → clasificar_intencion
                                            │
            ┌───────────────────────────────┼────────────────────────┐
      seguimiento                      devolucion                  cambio
            │                              │                          │
            ▼                              ▼                          ▼
    consultar_tracking         verificar_elegibilidad         verificar_stock
                                {router elegibilidad}        {router stock}
                            ┌──────┴──────┐               ┌─────┴─────┐
                        elegible      no_elegible    disponible    agotado
                            │              │              │            │
                            ▼              ▼              ▼            ▼
                  generar_etiqueta  derivar_humano  procesar_cambio  derivar_humano
                            │              │              │            │
                            └──────────────┴──────┬───────┴────────────┘
                                                  ▼
                                  redactar_respuesta → producir_resumen → END
```

### Nodos

| Nodo | Descripción |
|---|---|
| `recibir_solicitud` | Captura la solicitud (order_id + intent opcional) |
| `lookup_pedido` | Consulta el pedido en el OMS (DEMO: `orders.json`) |
| `clasificar_intencion` | Resuelve la intención (input cliente > pedido > default) |
| `consultar_tracking` | Recupera estado, hitos y ETA del carrier |
| `verificar_elegibilidad` | Política de devolución (plazo, categoría no devolvible, estado entregado) |
| `generar_etiqueta` | Etiqueta de retorno con SHA-256 sobre payload canonicalizado |
| `verificar_stock` | Stock real del SKU destino + plazo de cambio |
| `procesar_cambio` | Reserva inventario y agenda despacho |
| `derivar_humano` | Convergencia para casos no automatizables (SLA 24h) |
| `redactar_respuesta` | Mensaje empático al cliente (LIVE opt-in con LLM) |
| `producir_resumen` | Resumen ejecutivo del caso |

### Routers

| Router | Origen | Decisión |
|---|---|---|
| `intencion_router` | `clasificar_intencion` | `seguimiento` / `devolucion` / `cambio` |
| `elegibilidad_router` | `verificar_elegibilidad` | `elegible` / `no_elegible` |
| `stock_router` | `verificar_stock` | `disponible` / `agotado` |

## Datos DEMO

- `data/orders.json` — 5 pedidos que ejercitan los 5 caminos del grafo
- `data/return_policy.json` — plazo devolución (30d), plazo cambio (15d), categorías bloqueadas, carrier
- `data/inventory.json` — stock real por SKU para verificación de cambios

| Pedido | Cliente | Camino | Resultado esperado |
|---|---|---|---|
| ORD-001 | Carolina Vergara | seguimiento | 🟢 tracking entregado |
| ORD-002 | Felipe Morales | devolución dentro de plazo | 🟢 etiqueta `RET-ORD-002-...` con hash |
| ORD-003 | Patricia Sandoval | devolución vencida + categoría bloqueada | 🟡 derivado |
| ORD-004 | Javier Tapia | cambio talla, stock disponible | 🟢 reserva y despacho |
| ORD-005 | Andrea Bustos | cambio color, SKU destino sin stock | 🟡 derivado |

## API

| Endpoint | Descripción |
|---|---|
| `GET /health` · `/healthz` | estado + modo DEMO/LIVE |
| `GET /ready` | grafo compilable |
| `GET /metrics` | uptime, requests, latencia, modo |
| `POST /api/run` | ejecuta caso completo, retorna snapshot final |
| `GET /api/stream` | stream NDJSON con `stream_mode="values"` |
| `GET /` y `/web/` | UI estática del caso |

Validación de IDs con regex `^[A-Za-z0-9._:-]{1,64}$`, intent acotado a
`seguimiento | devolucion | cambio`. Middleware OAuth2/JWT opt-in
(`USE_OAUTH2=true`) y bucket rate-limit por IP — mismo patrón que casos 04/07/11/14.

## Modo DEMO / LIVE

- **DEMO** (sin `OPENAI_API_KEY`): respuesta de plantilla determinista. Funciona sin red.
- **LIVE** (con `OPENAI_API_KEY`): respuesta empática redactada por LLM. La lógica de
  elegibilidad, stock y etiqueta sigue siendo determinista.

## Ejecución

### Local

```bash
cd cases/15-ecommerce-postventa/backend
pip install -r requirements.txt
uvicorn src.api:app --host 0.0.0.0 --port 8015
# UI: http://localhost:8015/
```

### Docker

```bash
cd cases/15-ecommerce-postventa/backend
docker compose up --build
```

## Tests

```bash
cd cases/15-ecommerce-postventa/backend
python -m pytest tests/
# 33 tests: helpers, 3 routers, e2e por escenario, API, streaming NDJSON
```

## Stack

| Capa | Tecnología |
|---|---|
| Orquestación | LangGraph `StateGraph` + `MemorySaver` |
| API | FastAPI + uvicorn |
| LLM (opt-in) | OpenAI GPT-4o-mini |
| Auth (opt-in) | OAuth2/OIDC con `python-jose` |
| Empaquetado | Docker (python:3.11-slim, non-root) |
| UI | Vanilla HTML/CSS/JS con streaming NDJSON |
