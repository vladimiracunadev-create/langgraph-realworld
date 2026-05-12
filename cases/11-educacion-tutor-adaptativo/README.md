# Caso 11 — Tutor Adaptativo

> **Estado**: `OPERATIVO` · **Versión repo**: 4.9.0 · **Puerto**: 8011

Tutoría personalizada con IRT (Item Response Theory) simplificado. El agente diagnostica
el nivel del estudiante, selecciona ítems calibrados a su zona de desarrollo próximo,
simula su respuesta de forma determinista y adapta la dificultad en cada interacción.
Al cerrar la sesión emite un perfil actualizado y un reporte ejecutivo para docente e
institución.

## Objetivo de negocio

Las plataformas EdTech enfrentan el reto de personalizar el aprendizaje a escala:
un docente no puede adaptar el contenido para cada estudiante en tiempo real. Este
agente evalúa el nivel inicial con un pretest adaptativo, selecciona la ruta óptima
del banco de contenidos, presenta ítems calibrados al nivel del estudiante, analiza
errores para detectar conceptos erróneos y ajusta la dificultad y el formato
(explicación / ejemplo / práctica) en cada interacción, manteniendo un perfil de
aprendizaje persistente.

## Flujo LangGraph

```
cargar_perfil
   │
   ▼
{router diagnostico}
   ├─ sin_diagnostico → aplicar_diagnostico ┐
   └─ con_diagnostico ───────────────────── ┴→ seleccionar_item
                                                   │
                          ┌────────────────────────▼──────────────────────────┐
                          │  presentar_actividad → evaluar_respuesta          │
                          │              │                                    │
                          │              ▼                                    │
                          │       {router desempeño}                          │
                          │     ┌────────┼────────────────┐                   │
                          │  domina  error_conceptual  frustracion            │
                          │     │        │                │                   │
                          │     ▼        ▼                ▼                   │
                          │ aumentar  remediar         reducir                │
                          │     │        │                │                   │
                          │     └────────┴───────┬────────┘                   │
                          │                      ▼                            │
                          │              {router continuar}                   │
                          │           ┌─── continuar (loop) ──────────────────┘
                          └───────────┘
                                      └─── finalizar
                                              │
                                              ▼
                              actualizar_perfil → producir_reporte → END
```

### Nodos

| Nodo | Descripción |
|---|---|
| `cargar_perfil` | Carga estudiante, política, banco de ítems |
| `aplicar_diagnostico` | Pretest de 3 ítems para estimar habilidad inicial |
| `seleccionar_item` | Elige el ítem con dificultad más cercana a la habilidad (preferencia de formato) |
| `presentar_actividad` | Emite el ítem hacia la UI / cliente |
| `evaluar_respuesta` | Simulador determinista (per-student seed) clasifica como correcto / error conceptual / frustración |
| `aumentar_dificultad` | Sube la habilidad, registra concepto dominado, resetea racha de errores |
| `remediar_concepto` | Baja levemente la habilidad, registra concepto a remediar, incrementa racha |
| `reducir_dificultad` | Baja la habilidad de forma más agresiva (frustración), resetea racha |
| `actualizar_perfil` | Calcula métricas finales (tasa de acierto, promoción, recomendación) |
| `producir_reporte` | Reporte Markdown ejecutivo (LIVE opt-in con LLM) |

### Routers

| Router | Origen | Decisión |
|---|---|---|
| `diagnostico_router` | `cargar_perfil` | `sin_diagnostico` / `con_diagnostico` |
| `desempeno_router` | `evaluar_respuesta` | `domina` / `error_conceptual` / `frustracion` |
| `continuar_router` | después de cada ajuste | `continuar` (loop) / `finalizar` |

## Modelo IRT simplificado

- Escala de habilidad: **1.0 – 10.0**
- Cada ítem trae `dificultad` (en la misma escala) y `concepto`
- `gap = dificultad − habilidad`
- Clasificación determinista:
  - `gap ≤ 0` → **correcto**
  - `0 < gap < umbral_error_conceptual` → zona borderline (rng con seed)
  - `umbral_error_conceptual ≤ gap < umbral_frustracion` → **error_conceptual**
  - `gap ≥ umbral_frustracion` o racha de errores ≥ N → **frustracion**
- Adaptación (`tutor_policy.json`):
  - `delta_aumento = +0.4`
  - `delta_remediar = −0.3`
  - `delta_reducir = −0.6`

## Datos DEMO

- `data/students.json` — 3 estudiantes (STU-001 sin diagnóstico, STU-002 nivel medio, STU-003 nivel bajo)
- `data/item_bank.json` — 15 ítems de fracciones y porcentajes (dificultad 1.5 – 8.5)
- `data/tutor_policy.json` — umbrales, deltas, tope de sesión, criterios de promoción

## API

| Endpoint | Descripción |
|---|---|
| `GET /health` · `/healthz` | estado + modo DEMO/LIVE |
| `GET /ready` | grafo compilable |
| `GET /metrics` | uptime, requests, latencia, modo |
| `POST /api/run` | ejecuta sesión completa, retorna snapshot final |
| `GET /api/stream` | stream NDJSON con `stream_mode="values"` |
| `GET /` y `/web/` | UI estática del caso |

Validación de IDs con regex `^[A-Za-z0-9._:-]{1,64}$`. Middleware OAuth2/JWT opt-in
(`USE_OAUTH2=true`) y bucket rate-limit por IP — mismo patrón que casos 04/07/14.

## Modo DEMO / LIVE

- **DEMO** (sin `OPENAI_API_KEY`): simulador determinista por seed, reporte de plantilla.
- **LIVE** (con `OPENAI_API_KEY`): reporte ejecutivo redactado por LLM. El simulador
  sigue siendo determinista para mantener reproducibilidad pedagógica.

## Ejecución

### Local

```bash
cd cases/11-educacion-tutor-adaptativo/backend
pip install -r requirements.txt
uvicorn src.api:app --host 0.0.0.0 --port 8011
# UI: http://localhost:8011/
```

### Docker

```bash
cd cases/11-educacion-tutor-adaptativo/backend
docker compose up --build
```

## Tests

```bash
cd cases/11-educacion-tutor-adaptativo/backend
python -m pytest tests/
# 30 tests: helpers, routers, e2e por estudiante, API, streaming NDJSON
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
