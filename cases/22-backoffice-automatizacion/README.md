# Caso 22 — Backoffice: Automatización de Solicitudes

> [!NOTE]
> **Estado**: `✅ OPERATIVO` | **Versión repo**: 4.13.0 | **Puerto**: `8022`
> **Patrón**: 3 routers + loop de completitud + cadena de custodia SHA-256

Automatiza el ciclo completo de solicitudes de backoffice (altas, bajas, modificaciones,
reportes): parsea la solicitud, verifica identidad y permisos, valida completitud con loop,
ejecuta la operación en el sistema destino (CRM / HRIS / BI) y registra cada paso en un
log inmutable encadenado por hash SHA-256 para auditoría regulatoria.

---

## Flujo (LangGraph)

```
parsear_solicitud → clasificar_tipo_operacion → verificar_identidad
     → permisos_router
          ├─ sin_permisos → rechazar_solicitud ──┐
          └─ con_permisos → validar_datos_operacion
     → completitud_router
          ├─ faltantes ∧ iter<2 → solicitar_informacion → validar_datos_operacion
          └─ completos | tope  → ejecutar_operacion
     → ejecucion_router
          ├─ error_sistema → escalar_soporte ────┤
          └─ exitoso       → confirmar_solicitante
                                                 ├─→ registrar_log_auditoria → producir_resumen → END
```

### Nodos

| Nodo | Función |
|---|---|
| `parsear_solicitud` | Carga la solicitud (canal, solicitante, tipo, datos, prioridad) |
| `clasificar_tipo_operacion` | Resuelve sistema destino, endpoint y campos requeridos contra el catálogo |
| `verificar_identidad` | Empleado activo + tiene el permiso requerido + operación catalogada |
| `rechazar_solicitud` | Termina con `estado_final=rechazada` y motivo |
| `validar_datos_operacion` | Calcula `campos_faltantes` contra `campos_requeridos` |
| `solicitar_informacion` | Inyecta valores DEMO para los faltantes y reintenta (incrementa `iter_completitud`) |
| `ejecutar_operacion` | Llamada simulada determinista al sistema destino |
| `confirmar_solicitante` | Mensaje con referencia y SLA |
| `escalar_soporte` | Mensaje a `soporte_email` con sistema y error |
| `registrar_log_auditoria` | Construye cadena SHA-256 encadenada sobre todos los eventos |
| `producir_resumen` | Texto ejecutivo (DEMO determinista / LIVE con OpenAI) |

### Routers

- `permisos_router`: `permisos_ok → validar_datos_operacion`; si no → `rechazar_solicitud`
- `completitud_router`: faltantes y `iter<max_iter_completitud` → loop; si no → `ejecutar_operacion`
- `ejecucion_router`: `resultado.ok → confirmar_solicitante`; si no → `escalar_soporte`

---

## Cadena de custodia SHA-256

Cada eslabón del log de auditoría se calcula como:

```
hash_n = SHA256( hash_{n-1} | sort_json({idx, ts, solicitud_id, type, data}) )
```

Comenzando desde `hash_0 = "0"·64`. Cualquier alteración rompe la cadena. Mismo patrón que casos
06 (Compliance), 07 (Compras OC) y 15 (E-commerce etiquetas).

---

## Stack

| Capa | Tecnología |
|---|---|
| Orquestación | LangGraph `StateGraph` con `MemorySaver` |
| API | FastAPI + uvicorn |
| LLM (opcional) | OpenAI GPT-4o-mini para resumen (LIVE opt-in con `OPENAI_API_KEY`) |
| Auth | DEMO (sin token) + OAuth2/OIDC JWT opt-in (`USE_OAUTH2=true`) |
| Observabilidad | `/health`, `/ready`, `/metrics`, logs JSON con `trace_id` |

---

## Cómo correr

```bash
# Tests
cd cases/22-backoffice-automatizacion/backend
pip install -r requirements.txt
pytest

# Servidor (DEMO)
uvicorn src.api:app --host 0.0.0.0 --port 8022

# Con Docker
docker compose -f cases/22-backoffice-automatizacion/backend/compose.yml up --build
```

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET`  | `/health` · `/healthz` · `/ready` · `/metrics` | Observabilidad |
| `POST` | `/api/run` | Ejecuta el pipeline (`{thread_id, solicitud_id}`) |
| `GET`  | `/api/stream` | Streaming NDJSON con snapshots por nodo |
| `GET`  | `/` · `/web/` | UI mínima |

### Solicitudes DEMO

| ID | Tipo | Escenario | Resultado esperado |
|---|---|---|---|
| `SOL-001` | alta_usuario_crm | Brief limpio, permisos OK | `exitosa`, 0 iter completitud |
| `SOL-002` | modificacion_datos_cliente | Falta `nuevo_valor` | `exitosa`, iter ≥ 1 |
| `SOL-003` | baja_empleado_hris | Solicitante sin permiso | `rechazada` |
| `SOL-004` | reporte_ventas_mensual | `falla_simulada=true` en catálogo | `escalada` a soporte |

---

## Datos (`data/`)

| Archivo | Contenido |
|---|---|
| `solicitudes.json` | 4 solicitudes cubriendo los 3 caminos terminales |
| `empleados.json` | 4 empleados con roles y matriz de permisos |
| `operaciones_catalog.json` | 4 operaciones (CRM, HRIS, BI) con campos requeridos y SLA |
| `policy.json` | `max_iter_completitud=2`, email de soporte, retención auditoría |

---

> [!TIP]
> Patrón análogo: casos **06** (Compliance, cadena de custodia) y **07** (Compras, OC inmutable).
