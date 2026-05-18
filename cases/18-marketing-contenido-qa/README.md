# Caso 18 — Marketing de Contenido con QA

> [!NOTE]
> **Estado**: `✅ OPERATIVO` | **Versión repo**: 4.12.0 | **Puerto**: `8018`
> **Patrón**: pipeline con dos loops condicionales (tono y hechos)

Automatiza la producción de contenido de marketing con un pipeline de calidad integrado:
genera el borrador a partir del brief, lo audita contra la guía de marca, verifica los
hechos contra fuentes autorizadas, optimiza SEO y lo somete a aprobación editorial.

---

## Flujo (LangGraph)

```
parsear_brief → generar_borrador
     → revisar_estilo_marca
          ├─ ok=False ∧ iter<2 → reescribir_tono → revisar_estilo_marca
          └─ ok=True            → verificar_hechos
     → verificar_hechos
          ├─ ok=False ∧ iter<2 → corregir_hechos → verificar_hechos
          └─ ok=True            → optimizar_seo
     → optimizar_seo → aprobacion_editor → publicar_contenido → producir_resumen → END
```

### Nodos

| Nodo | Función |
|---|---|
| `parsear_brief` | Carga brief (formato, audiencia, tono, keywords, hechos obligatorios) |
| `generar_borrador` | Render determinista por formato (blog_post / email / landing) |
| `revisar_estilo_marca` | Detecta palabras prohibidas, no preferidas, frases largas |
| `reescribir_tono` | Sustituye palabras prohibidas/no preferidas — incrementa `iter_estilo` |
| `verificar_hechos` | Contrasta contra `fact_sources.json`, detecta alucinaciones y hechos faltantes |
| `corregir_hechos` | Retira alucinaciones e inyecta hechos verificados — incrementa `iter_hechos` |
| `optimizar_seo` | Densidad de keywords, presencia de H1 y CTA |
| `aprobacion_editor` | Score global ponderado (hechos 0.5 · estilo 0.3 · SEO 0.2) → riesgo + decisión |
| `publicar_contenido` | Compone contenido final y métricas |
| `producir_resumen` | Texto ejecutivo (DEMO determinista o LIVE con OpenAI) |

### Routers

- `estilo_router`: si `estilo.ok=False` y `iter_estilo<max` → loop; si no → `verificar_hechos`
- `hechos_router`: si `hechos.ok=False` y `iter_hechos<max` → loop; si no → `optimizar_seo`

---

## Stack

| Capa | Tecnología |
|---|---|
| Orquestación | LangGraph `StateGraph` con `MemorySaver` |
| API | FastAPI + uvicorn |
| LLM (opcional) | OpenAI GPT-4o-mini (LIVE opt-in con `OPENAI_API_KEY`) |
| Auth | DEMO (sin token) + OAuth2/OIDC JWT opt-in (`USE_OAUTH2=true`) |
| Observabilidad | `/health`, `/ready`, `/metrics`, logs JSON con `trace_id` |

---

## Cómo correr

```bash
# Tests
cd cases/18-marketing-contenido-qa/backend
pip install -r requirements.txt
pytest

# Servidor (DEMO)
uvicorn src.api:app --host 0.0.0.0 --port 8018

# Con Docker
docker compose -f cases/18-marketing-contenido-qa/backend/compose.yml up --build
```

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET`  | `/health` · `/healthz` · `/ready` · `/metrics` | Observabilidad |
| `POST` | `/api/run` | Ejecuta el pipeline (`{thread_id, brief_id}`) |
| `GET`  | `/api/stream` | Streaming NDJSON con snapshots por nodo |
| `GET`  | `/` · `/web/` | UI mínima |

### Briefs DEMO

| ID | Formato | Escenario | Resultado esperado |
|---|---|---|---|
| `BR-001` | blog_post | Brief limpio | Verde, sin iteraciones de hechos |
| `BR-002` | email | 2 claims sin respaldo | Iter. hechos ≥ 1, alucinaciones retiradas |
| `BR-003` | landing | 3 claims sin respaldo + tono legacy | Iter. hechos ≥ 1, riesgo amarillo/rojo |

---

## Datos (`data/`)

| Archivo | Contenido |
|---|---|
| `briefs.json` | 3 briefs (BR-001/002/003) con `hechos_obligatorios` y `claims_riesgosos` |
| `brand_style.json` | Voz oficial, palabras prohibidas, palabras preferidas, límites de estilo, CTAs |
| `fact_sources.json` | 6 fuentes autorizadas con claims verificados |
| `quality_rules.json` | Umbrales (estilo 80, hechos 90), penalizaciones, ponderación riesgo |

---

> [!TIP]
> Patrón análogo: caso **21** (Docs Auto) — mismo esquema de loop QA con tope de iteraciones.
