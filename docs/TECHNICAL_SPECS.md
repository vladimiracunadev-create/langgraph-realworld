# ⚙️ Especificaciones Técnicas

> [!NOTE]
> **Versión**: 3.7.0 | **Estado**: Industrial | **Audiencia**: Senior Backend Engineers, SREs

Este documento rompe la caja negra del servidor y describe las tecnologías subyacentes e interacciones hardcore construidas en los pipelines de **LangGraph Realworld**.

## 🚀 Stack Core Tecnológico

| Capa | Tecnología Principal | Propósito |
|---|---|---|
| **API Backend** | `FastAPI` (Python 3.11) | Manejo concurrente de rutas de streaming REST. |
| **Servidor App** | `Uvicorn` | Interfaz ASGI rápida de servicio. |
| **Orquestación AI** | `LangGraph` + `LangChain` | Construcción de grafos cíclicos con checkpoints de memoria. |
| **Deployment** | `Docker` & `Docker Compose` | Aislamiento y orquestación multi-puerto paralela. |
| **Frontend** | Interfaz `Vanilla` | Fetching de HTTP Streams sin engordar bundles. |

## 📡 Pipeline de Streaming NDJSON

Uno de los principales hitos técnicos implementados en este repositorio es el **Streaming Real-Time Asíncrono**. Los grafos corporativos de LangGraph son lentos por naturaleza debido al latencia I/O de las APIs y las bases de datos.

Para dar una "Experiencia Fluida", los backends de FastAPI no esperan que el LangGraph de turno termine todo el proceso.

1. Se compila el `StateGraph`.
2. Se lanza a través de `graph.stream()`.
3. FastAPI captura cada "Tick" / "State Update" del grafo de manera asíncrona usando generadores de Python (`yield`).
4. Genera una carga parcial en forma de `Newline Delimited JSON` (NDJSON).
5. Transmite el paquete a la UI mediante un `StreamingResponse`.

### El Output en JS (Browser):
El cliente decodifica utilizando `TextDecoder` el stream de Readable Body que va cayendo en ráfagas:
```javascript
// NDJSON format arrival in the client:
{"event": "enriched", "user": "msmith"}
{"event": "approval_checked", "status": "APPROVED"}
```

## 🔀 Restricciones y Routing Condicional

Para domar al LLM en entornos críticos (como Mesa de Ayuda TI o Analista Financiero), hemos levantado un diseño arquitectónico predecible:

- **Bypass Temprano:** LangGraph utiliza *Conditional Edges* para detener ataques de inyección (`unsupported`), evadiendo Nodos operativos y forzando la terminación del Request casi sin cómputo.
- **Human-In-The-Loop (HITL):** En Casos Críticos, la máquina suspende su ejecución (o simula la suspensión). La API evalúa reglas de control perimetrales y transicionales (Managers) y aprueba antes de llegar al nodo final `execute_action`.
- **Estandarización de Fallbacks:** Todos los nodos incluyen validación estricta nativa (`is_live()`) operando sobre Data Classes y TypedDict.
