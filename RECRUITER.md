# 👔 Guía Estratégica para Reclutadores (RECRUITER)

> **Executive Summary**: Este repositorio demuestra maestría técnica en el orquestación de Agentes LLM con estado, DevOps avanzado y diseño de sistemas resilientes preparados para producción.

---

## 🎯 Valor de Negocio y Visión

Este proyecto no es solo una colección de scripts; es un **Agentic Resilience Hub** que resuelve problemas críticos de negocio mediante IA:
- **Automatización de Procesos**: Reducción de tiempos en tareas de bajo valor (Screening, Soporte).
- **Confiabilidad**: Arquitectura diseñada para fallar con gracia y recuperarse (Zero Data Loss).
- **Escalabilidad**: Contenerización estandarizada para despliegues rápidos en la nube.

---

## 🏗️ Decisiones Arquitectónicas Clave

1.  **LangGraph sobre cadenas lineales**: Permite flujos cíclicos complejos, re-intentos inteligentes y razonamiento iterativo.
2.  **Streaming NDJSON**: Feedback instantáneo al usuario, mejorando radicalmente la UX de aplicaciones de IA.
3.  **Persistencia en SQLite**: Implementación de checkpoints para asegurar la continuidad del flujo en entornos inestables.
4.  **Capa de Resiliencia (Tenacity)**: Separación de la lógica de negocio de la lógica de reintento de infraestructura.

---

## 🏆 Caso de Éxito: Caso 09 (Screening + Agenda)

Este es nuestro **modelo de referencia** que demuestra el stack completo:
- **Frontend**: Dashboard Glassmorphism con streaming en tiempo real.
- **Backend API**: FastAPI asíncrono.
- **Motor AI**: LangGraph con 5+ nodos de razonamiento y herramientas.
- **DevOps**: Docker + K8s + Smoke Testing automatizado.

---

## 🛠️ Habilidades Técnicas Demostradas

| Área | Competencias |
| :--- | :--- |
| **Backend** | Python 3.11+, FastAPI, Asincronía, Logging Estructurado. |
| **IA / Agentes** | LangGraph, LangChain, Prompt Engineering, Guardrails. |
| **DevOps** | CI/CD (GitHub Actions), Docker, Kubernetes, Hub CLI (Orchestration). |
| **Seguridad** | Secret Scanning, Non-Root UID, Network Policies. |
| **Quality Assurance** | Ruff (Linting), Smoke Tests, Walkthroughs técnicos. |

---

## 🧭 Tour Guiado de Evaluación (5 min)

Si tiene poco tiempo, le recomiendo seguir este recorrido:
1.  **Código Central**: Vea la definición del grafo en [`cases/09-rrhh-screening-agenda/backend/src/graph.py`](cases/09-rrhh-screening-agenda/backend/src/graph.py).
2.  **Resiliencia**: Observe cómo manejamos las APIs externas en [`cases/09-rrhh-screening-agenda/backend/src/integrations.py`](cases/09-rrhh-screening-agenda/backend/src/integrations.py).
3.  **Infraestructura**: Revise los manifiestos de K8s en [`k8s/cases/09-rrhh-screening-agenda/`](k8s/cases/09-rrhh-screening-agenda/).

---

## 📊 Madurez Técnica

Nuestra arquitectura adhiere a los principios de **12-Factor App** y **Clean Code**, garantizando que el proyecto sea mantenible y fácil de escalar por un equipo de ingeniería.

---
> [!TIP]
> **¿Desea una entrevista técnica?** Estoy preparado para discutir en profundidad cualquiera de las decisiones documentadas en nuestra [Arquitectura Detallada](docs/ARCHITECTURE.md).
