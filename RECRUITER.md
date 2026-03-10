# 👔 Guía Estratégica para Reclutadores (RECRUITER)

> **Versión**: 3.4.0 | **Estado**: Industrial | **Audiencia**: Reclutadores, Hiring Managers
>
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
5.  **Arquitectura Híbrida (Cost-Efficiency)**: Capacidad de cambiar entre motores Mock (para pruebas sin coste) y Motores IA Reales sin modificar código, optimizando el presupuesto de desarrollo.

---

## 🏆 Casos de Éxito Industriales (v3.4.0)

Este repositorio destaca tres implementaciones de nivel empresarial que demuestran versatilidad y robustez:

1.  **Caso 09 (RRHH Screening + Agenda)**: El estándar de oro en resiliencia. Manejo de APIs inestables, persistencia de estado y streaming de alta fidelidad.
2.  **Caso 10 (Onboarding Proactivo)**: Orquestación compleja con ramificaciones basadas en roles y sistema de notificaciones multicanal resiliente.
3.  **Caso 13 (BI Data Analyst)**: Maestría en integración de datos relacionales, generación de SQL dinámico y visualización reactiva con dashboards premium.

---

## 📊 Caso de Éxito: Caso 13 (BI Data Analyst)

Demuestra la capacidad de integrar agentes con sistemas de bases de datos relacionales:
- **Agente SQL**: Generación precisa de queries complejas (Joins, Aggregations).
- **Visualización**: Dashboard con gráficos dinámicos (**Chart.js**) que responden en tiempo real.
- **Modo Dual**: Funciona offline (Demo) o con LLM avanzado, optimizando costos de nube.

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
3.  **Análisis de Datos**: Vea la generación de SQL y visualización en [`cases/13-bi-analista-datos/backend/src/graph.py`](cases/13-bi-analista-datos/backend/src/graph.py).
4.  **Infraestructura**: Revise los manifiestos de K8s en [`k8s/cases/09-rrhh-screening-agenda/`](k8s/cases/09-rrhh-screening-agenda/).

---

## 📊 Madurez Técnica

Nuestra arquitectura adhiere a los principios de **12-Factor App** y **Clean Code**, garantizando que el proyecto sea mantenible y fácil de escalar por un equipo de ingeniería.

---
> [!TIP]
> **¿Desea una entrevista técnica?** Estoy preparado para discutir en profundidad cualquiera de las decisiones documentadas en nuestra [Arquitectura Detallada](docs/ARCHITECTURE.md).
