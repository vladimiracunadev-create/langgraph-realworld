# 🤖 Caso 09: RR.HH. Screening + Agenda (Standardized)

**Detección de talento y agendamiento automatizado** con una arquitectura de agentes altamente resiliente. Este caso sirve como el **estándar de oro** del repositorio para implementaciones de producción.

## 🏗️ Arquitectura del Flujo

```mermaid
graph TD
  START((Inicio)) --> Load[Cargar Job + Candidatos]
  Load --> Score{Scoring Loop}
  Score -->|Procesar 1| SNode[score_one]
  SNode -->|Resilient Call| Integrations[integrations.py]
  Integrations -->|Tenacity Retry| LLM[LLM/Parsing Simulation]
  SNode --> Score
  Score -->|Completado| Shortlist[build_shortlist]
  Shortlist --> Schedule[schedule_interviews]
  Schedule --> END((Fin))

  subgraph "Capa de Resiliencia"
    Tenacity[Exponential Backoff]
    Degradation[Graceful Degradation]
    Recursion[Recursion Limit: 50]
  end
```

---

## 🛡️ Resiliencia y Guardrails (Enterprise Grade)

| Característica | Implementación | Propósito |
| :--- | :--- | :--- |
| **Retries** | `tenacity` (backoff exponencial) | Manejo de errores intermitentes en APIs externas. |
| **Error Handling** | `try/except` en nodos del grafo | Evita el colapso del flujo; captura errores y continúa. |
| **Step Limits** | `recursion_limit: 50` | Previene bucles infinitos en el agente. |
| **Checkpoints** | `SqliteSaver` | Persistencia de estado e idempotencia. |
| **Health Checks** | `/health` & `/ready` | Monitoreo de liveness y readiness para CI/CD. |

---

## 🛠️ Tech Stack

- **Core**: [LangGraph](https://github.com/langchain-ai/langgraph) (Orquestación de agentes con estado).
- **Backend API**: [FastAPI](https://fastapi.tiangolo.com/) (Streaming NDJSON).
- **Resilience**: [Tenacity](https://tenacity.readthedocs.io/) (Estrategias de reintento).
- **Quality**: [Ruff](https://beta.ruff.rs/docs/) (Linting & Formatting).
- **Container**: [Docker](https://www.docker.com/) (Entorno reproducible).

---

## 🚀 Cómo empezar

### Ejecución Local

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.api:app --reload --port 8009
```
Abre: `http://localhost:8009`

### Validación con Docker (Smoke Tests)

Para validar la resiliencia y el flujo completo:
```bash
cd backend
docker compose -f compose.smoke.yml up --build --abort-on-container-exit
```

---

## 🧭 Activación "Real IA" (Paso a Paso)

Para habilitar el cerebro de agentes LangGraph (OpenAI) en lugar de la demo:

1. **Localiza la carpeta**: `cases/09-rrhh-screening-agenda/backend/`
2. **Crea el archivo `.env`**:
   ```env
   OPENAI_API_KEY=tu_key_aqui
   MODEL=gpt-4o-mini
   ```
3. **Inicia el servidor real**:
   ```bash
   uvicorn src.api:app --port 8009
   ```

**Ubicación física en el disco:**
```text
[PROYECTO_RAIZ]
└── cases/
    └── 09-rrhh-screening-agenda/
        └── backend/
            └── .env  <-- ESTE ES EL ARCHIVO QUE DEBES CREAR
```

---
> [!IMPORTANT]
> Los logs están configurados en formato **JSON estructurado** para facilitar la integración con Datadog, ELK o CloudWatch.
