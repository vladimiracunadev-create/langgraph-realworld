# 🏗️ Arquitectura del Sistema (ARCHITECTURE)

Este documento describe la estructura técnica de **LangGraph Realworld**, centrándose en la orquestación de agentes con estado y el motor de resiliencia del Caso 09.

---

## 🛰️ Visión General

El proyecto está diseñado como un **Monorepo de Casos de Uso**, donde cada "caso" es un ecosistema autocontenido que utiliza un núcleo común de patrones agenticos.

```mermaid
graph TD
  subgraph "Capa de Presentación"
    UI[Dashboards Premium - Glassmorphism]
    CLI[Hub CLI - python hub.py]
  end

  subgraph "Capa de Aplicación (FastAPI)"
    API[Backend API - Entorno Docker]
    Stream[Streaming NDJSON / events]
  end

  subgraph "Motor de Agentes (LangGraph)"
    LG[StateGraph / Nodes]
    Check[SqliteSaver - Checkpoints]
    Tools[Tools / Integrations]
  end

  subgraph Resilience ["Capa de Resiliencia"]
    Ten[Tenacity - Exponential Backoff]
    Deg[Graceful Degradation Logic]
    Guard[Guardrails / Step Limits]
  end

  UI --> API
  CLI --> API
  API --> LG
  LG --> Check
  LG --> Tools
  Tools --> Resilience
  Resilience --> Integrations[External APIs / Stubs]
```

---

## 🔄 Flujo de Ejecución (Estandarizado)

El Caso 09 (Screening + Agenda) actúa como el **modelo de referencia** para el flujo de datos:

1.  **Ingesta**: Carga de datos de entrada (JSON/PDF) y persistencia en el `State`.
2.  **Iteración Resiliente**: Cada nodo del grafo ejecuta llamadas a herramientas envueltas en decoradores de reintento (`tenacity`).
3.  **Manejo de Fallos**: Si una herramienta falla definitivamente, el nodo captura la excepción y emite un evento `error_node` al stream, permitiendo que el flujo continúe (Degradación Graciosa).
4.  **Checkpointing**: Cada paso se guarda en SQLite, permitiendo reanudar el flujo en caso de interrupción del servidor.

---

## 🛠️ Estándares de Implementación

- **LangGraph**: Uso estricto de `StateGraph` con `Annotated` para reducers de estado (ej: `operator.add` para logs de eventos).
- **FastAPI**: Endpoints asíncronos con soporte para `StreamingResponse` para feedback en tiempo real.
- **Docker**: Orquestación multietapa para separar el build de la ejecución, minimizando el tamaño de la imagen.
- **Observabilidad**: Logs en formato JSON estructurado listos para ser ingeridos por pilas ELK o CloudWatch.

---

## ⚙️ Integración Continua (CI/CD)

```mermaid
sequenceDiagram
    participant Dev as Desarrollador
    participant GH as GitHub Repo
    participant GA as GitHub Actions
    participant Docker as Container Registry

    Dev->>GH: git push origin main
    GH->>GA: Trigger: ci.yml
    GA->>GA: Linting (Ruff/Markdown)
    GA->>GA: Seguridad (Secret Scanning)
    GA->>GA: Build Multi-arch Image
    GA->>GA: Smoke Test (compose.smoke.yml)
    GA-->>Dev: Notificación de Salud del Repo
```

---

## 📚 Documentos Relacionados

- 📚 [Specs Técnicas](TECHNICAL_SPECS.md): Detalle del stack y protocolos.
- 📋 [Requisitos](REQUIREMENTS.md): Hardware y software necesario.
- 🛡️ [Seguridad](../SECURITY.md): Política de protección de datos y secretos.
