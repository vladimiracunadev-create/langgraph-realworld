# Caso 13: Analista de Datos BI

> [!IMPORTANT]
> **Estado**: `INDUSTRIAL` | **Versión**: 3.9.0 | **Referencia**: SQL seguro + Data Viz

Agente conversacional de Business Intelligence que permite consultar una base de datos SQLite
mediante lenguaje natural, generando SQL validado, visualizaciones con Chart.js y respuestas
explicativas. El SQL está endurecido: solo lectura, sin comentarios, con límite de filas.

---

## Características de seguridad SQL

- Solo `SELECT` y CTEs — ninguna operación de escritura o modificación.
- Comentarios SQL bloqueados para prevenir bypass de validación.
- Sin objetos internos de SQLite (`sqlite_*`).
- Sin múltiples sentencias en una sola consulta.
- Límite máximo de filas configurable.
- Conexión SQLite en modo solo lectura.

---

## Integraciones opcionales

| Servicio | Variable | Descripción |
|:---|:---|:---|
| OpenAI | `OPENAI_API_KEY` | Traduce lenguaje natural a SQL |

Funciona en **DEMO** sin `OPENAI_API_KEY` usando consultas predefinidas.

---

## Controles de seguridad del contenedor

- Imagen Docker: `python:3.11.10-slim`, usuario `appuser` (non-root).
- `DEMO_AUTH_TOKEN` y `RATE_LIMIT_RPM` opcionales para exposición externa controlada.

---

## Cómo ejecutar

```bash
# Con Docker
docker compose up case13

# En local
cd cases/13-bi-analista-datos/backend
uvicorn src.api:app --reload --port 8013
```

UI del caso: [http://localhost:8013/web/](http://localhost:8013/web/)

---

> [!TIP]
> Ver [SECURITY.md](../../SECURITY.md) para el detalle de los controles de hardening activos en este caso.
