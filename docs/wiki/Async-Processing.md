# Procesamiento Asíncrono y Resiliencia (Async) ⚡

Este documento describe cómo gestionamos los flujos de larga duración, el streaming de eventos y la resiliencia en los agentes de **LangGraph Realworld**.

---

## 🛰️ Arquitectura de Streaming

Utilizamos **FastAPI** para exponer flujos asíncronos mediante `StreamingResponse`. Esto permite que el usuario vea el progreso del agente paso a paso sin esperar a que termine toda la tarea.

### Flujo de Datos
1.  **Request**: El cliente inicia una tarea vía POST/GET.
2.  **Orquestación**: LangGraph inicia la ejecución del grafo.
3.  **Streaming**: Cada nodo emite eventos que se envían como **NDJSON** (Newline Delimited JSON).
4.  **Feedback**: La UI procesa cada línea y actualiza el estado en tiempo real.

---

## 🏗️ Patrones de Resiliencia

Para asegurar que los agentes no fallen ante errores transitorios (ej: timeout de una API), aplicamos el patrón **Retry** con la librería `tenacity`.

### Estándar de Implementación
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def call_external_llm(data):
    # Lógica de llamada externa
    pass
```

---

## 🏥 Observabilidad en Tiempo Real

Dada la naturaleza asíncrona, el monitoreo tradicional no es suficiente. Por ello, hemos estandarizado:

### Contrato de Salud Estructurado
Los servicios deben exponer un estado de salud que incluya telemetría básica:
- `{"status": "ok", "ts": 1700000000}`: Indica que el bucle de eventos está respondiendo.

### Logs Estructurados
Los logs deben emitirse en formato JSON para facilitar su rastreo en flujos concurrentes:
```json
{"ts": "2026-02-13 12:55:02", "level": "INFO", "name": "api", "msg": "Stream iniciado para thread_id: test-123"}
```

---

## 🧪 Estrategia de Testing para Async

Para evitar fallos en el CI causados por servicios que aún no están listos o puertos ocupados, seguimos la siguiente política:

1.  **Unit Tests (`test_*.py`)**: Deben ser 100% aislados. No requieren que el servidor esté activo. Se ejecutan con `pytest`.
2.  **Smoke Tests (`smoke_integration.py`)**: Validan la conectividad real con el backend (Puerto **8009**). Estos se ejecutan EXCLUSIVAMENTE dentro del entorno Docker mediante `compose.smoke.yml`.

---

## 📚 Enlaces de Interés
- [Especificaciones Técnicas](../TECHNICAL_SPECS.md): Detalle del stack.
- [Guía de Instalación](../INSTALL.md): Cómo levantar el entorno Docker.
