# 🚀 LangGraph – Agentic Resilience Hub

[![CI](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml/badge.svg)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml)
[![Security Scan](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml/badge.svg)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Portafolio de arquitectura de agentes con estado, flujos cíclicos y capas de resiliencia empresarial.** Este repositorio demuestra cómo llevar LangGraph a producción con un enfoque en seguridad, observabilidad y recuperación ante fallos.

---

## �️ Implementación Industrial (v3.2.0)

Para elevar el proyecto a un estándar profesional "Real-World", se han realizado las siguientes modificaciones:

1.  **Punto de Entrada Unificado**: Consolidación del portal premium en **`index.html`** (eliminando `indexado.html`).
2.  **Diseño Premium**: Implementación de tipografía **Inter** y efectos **Glassmorphism** avanzados.
3.  **Resiliencia e Integridad**: Persistencia con `SqliteSaver` y validación de estado mediante **Pydantic**.
4.  **Telemetría Ready**: Rastrabilidad de flujos con `trace_id` inyectado en logs JSON.
5.  **Dual-Mode Execution**: Soporte para **Modo IA Real** (LLM) y **Modo Instant Demo** (Mock).
6.  **Interconectividad**: Sincronización global de links y reconstrucción de la Wiki técnica.

> [!TIP]
> Consulta el historial técnico detallado en el [CHANGELOG.md](CHANGELOG.md).

### 🛠️ Taxonomía de Implementación
Para asegurar la transparencia técnica, cada caso se clasifica en uno de estos tres niveles:
- **🛡️ Industrial (v3.2)**: Casos de referencia con FastAPI, Streaming, Pydantic y Observabilidad (Caso 09).
- **🏗️ Scaffold (v1.0)**: Estándar base con orquestación y Docker Ready (Caso 01).
- **📜 Legacy**: Plantillas de arquitectura para futura expansión.

---

---

## 🧭 ¿Por dónde empezar? (Rutas Personalizadas)

| Perfil | Ruta Recomendada | Objetivo |
| :--- | :--- | :--- |
| **💼 Reclutador / Manager** | [**Guía para Reclutadores**](RECRUITER.md) | Entender el valor de negocio y madurez técnica. |
| **💻 Desarrollador / DevOps** | [**Caso 09 (Reference Case - Industrial)**](cases/09-rrhh-screening-agenda/README.md) | Explorar código real: FastAPI, streaming, Pydantic y grafos. |
| **🔒 Experto en Seguridad** | [**SECURITY.md**](SECURITY.md) | Analizar protocolos de SAST y Hardening. |
| **🐣 Principiante** | [**Guía para Principiantes**](docs/BEGINNERS_GUIDE.md) | Primeros pasos con el repo y el Hub. |

---

## 🏗️ Arquitectura de Alto Nivel

```mermaid
flowchart LR
  UI[Dashboards Premium] -->|streaming| API[FastAPI Server]
  API --> LG[LangGraph Engine]
  LG --> CK[(SQLite Checkpoints)]
  LG --> TL[Resilient Tools Layer]
  TL --> EXT[External Systems]
```

---

## 🚀 Operación del Hub (Orquestación)

Gestiona los 25 casos de forma centralizada. El **Hub CLI** (`hub.py`) es una herramienta en Python que orquesta tanto la ejecución local como el lanzamiento de contenedores Docker.

```bash
# 1. Operación Directa (Nivel 1: Laboratorio)
python serve_site.py             # Portal 8080
python cases/09-*/backend/mock_api.py   # Backend 8009 (Modo Demo)

# 2. Operación vía Hub (Nivel 2: Orquestación)
python hub.py list      # Listar casos y su estado
python hub.py doctor    # Verificar salud del entorno
make case-up CASE=09    # Lanzar Caso 09 (Usa Docker si está disponible)
```

### 🧠 Activación de la IA Real (OpenAI)
Para habilitar el razonamiento avanzado en el Caso 09 (sustituyendo el modo demo):
1. **API Key**: Crea un `.env` en `cases/09-*/backend/` con `OPENAI_API_KEY=vuestro_token`.
2. **Backend**: Ejecuta `uvicorn src.api:app --port 8009` desde la misma carpeta.
3. **Verificación**: El portal detectará automáticamente el cambio a "Modo IA Real".

> [!NOTE]
> Para una guía completa de despliegue (Docker, K8s, Local), consulta la [**Guía de Instalación**](docs/INSTALL.md).

---

## 🛡️ Seguridad y Gobernanza

Este repositorio aplica un modelo de **Defensa en Profundidad**:

- 🔍 **Secret Scanning**: Auditoría constante con `detect-secrets`.
- 📦 **Non-Root Containers**: Aislamiento de privilegios en todas las imágenes.
- 🔄 **Exponential Backoff**: Resiliencia ante fallos de APIs externas mediante `tenacity`.
- 📜 **Killed.md**: Documentación de antipatrones prohibidos en el desarrollo.

---

## 📚 Documentación Técnica Completa

- 🏗️ [**Arquitectura Detallada**](docs/ARCHITECTURE.md): Diagramas y motor de persistencia.
- 🛠️ [**Especificaciones Técnicas**](docs/TECHNICAL_SPECS.md): Tech stack y contratos de API.
- 📋 [**Requisitos del Sistema**](docs/REQUIREMENTS.md): Hardware y compatibilidad.
- 🛣️ [**Roadmap**](ROADMAP.md): Hitos y visión a futuro.

---


---
> [!IMPORTANT]
> **He diseñado este repositorio para que sea fácil de auditar.** El **Caso 09** es el punto de referencia para evaluar mi capacidad de integrar IA en flujos de trabajo empresariales complejos.
