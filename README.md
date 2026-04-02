# LangGraph Realworld

[![CI](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml)
[![Security Scan](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Portafolio de casos de uso con LangGraph, FastAPI y demos empresariales. El repositorio combina una capa documental fuerte con cinco casos operables: 01, 02, 09, 10 y 13.

---

## Implementación Industrial (v3.6.0)

El estándar actual del repositorio se apoya en estos pilares:

1. **Portal unificado**: `index.html` como entrada principal para navegar el portafolio.
2. **Casos de referencia reales**: backends FastAPI y UIs activas en los casos 01, 02, 09, 10 y 13.
3. **Estado tipado**: contratos explícitos de estado con `TypedDict` y flujos compatibles con LangGraph.
4. **Observabilidad**: endpoints `/health` y `/ready`, además de trazabilidad por eventos o `trace_id` según el caso.
5. **Modo dual**: demos offline y ruta clara para activar integraciones reales mediante `.env.example`, `.env` y variables de entorno.
6. **Operación portable**: ejecución por Docker, Hub CLI o entorno local según el caso.
7. **Activación profesional de APIs**: portal y UIs con formulario para capturar credenciales opcionales, enlazar su origen y exportar el `.env` por caso.

> [!TIP]
> Consulta el detalle técnico en [CHANGELOG.md](CHANGELOG.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/TECHNICAL_SPECS.md](docs/TECHNICAL_SPECS.md) y [docs/INSTALL.md](docs/INSTALL.md).

### Taxonomía de Implementación

- **Operational (v3.6.0)**: caso 01 con backend real, ruteo omnicanal, modo DEMO/LIVE, UI operativa y configuración opcional desde interfaz.
- **Industrial (v3.6.0)**: casos con backend real, streaming, estado tipado, observabilidad, documentación operativa y activación guiada de APIs.
- **Legacy / Scaffold**: demos o plantillas listas para evolucionar sin pretender hoy el mismo nivel operativo.

### Estado de los Casos Clave

| Case ID | Nombre | Estado | Stack principal |
| :--- | :--- | :--- | :--- |
| **01** | [Soporte Cliente Omnicanal](cases/01-soporte-cliente-omnicanal/README.md) | `OPERATIVO` | FastAPI + LangGraph + Routing + DEMO/LIVE |
| **02** | [Mesa de Ayuda TI](cases/02-mesa-ayuda-ti-runbooks/README.md) | `OPERATIVO` | FastAPI + CMDB + LangGraph + HITL |
| **09** | [RRHH Screening Agenda](cases/09-rrhh-screening-agenda/README.md) | `INDUSTRIAL` | FastAPI + LangGraph + MemorySaver + Resilience |
| **10** | [Onboarding Empleados](cases/10-onboarding-empleados/README.md) | `INDUSTRIAL` | FastAPI + RBAC + Integrations + MemorySaver |
| **13** | [BI Data Analyst](cases/13-bi-analista-datos/README.md) | `INDUSTRIAL` | FastAPI + SQL Agent + Chart.js + DEMO/LLM |

---

## ¿Por dónde empezar?

| Perfil | Ruta recomendada | Qué mirar |
| :--- | :--- | :--- |
| Dev / DevOps | [Caso 01](cases/01-soporte-cliente-omnicanal/README.md) | Triage omnicanal, routing y fallback DEMO/LIVE |
| IT Admin / SRE | [Caso 02](cases/02-mesa-ayuda-ti-runbooks/README.md) | Enriquecimiento de perfil, HITL (aprobaciones), control de excepciones, UI de Terminal dinámica |
| Dev / DevOps | [Caso 09](cases/09-rrhh-screening-agenda/README.md) | Resiliencia, streaming y activación opcional de integraciones |
| Dev / DevOps | [Caso 10](cases/10-onboarding-empleados/README.md) | Flujo empresarial, RBAC e integraciones |
| Analista / BI | [Caso 13](cases/13-bi-analista-datos/README.md) | SQL seguro, visualización y activación opcional de LLM |
| Recruiter / Hiring Manager | [docs/RECRUITER.md](docs/RECRUITER.md) | Resumen ejecutivo, señales de seniority y ruta de evaluación |
| Principiante | [docs/BEGINNERS_GUIDE.md](docs/BEGINNERS_GUIDE.md) | Mapa del repositorio |
| Seguridad | [SECURITY.md](SECURITY.md) | Postura de hardening y manejo de secretos |

---

## Activar APIs opcionales

- Copia `backend/.env.example` a `backend/.env` en el caso que quieras llevar a LIVE.
- O abre el portal raíz y usa `Configurar APIs del portfolio` para completar credenciales, ver dónde obtenerlas y exportar el `.env` por caso.
- Si no agregas credenciales, los casos siguen funcionando en DEMO.
