# LangGraph Realworld

[![CI](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml)
[![Security Scan](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Portafolio de casos de uso con LangGraph, FastAPI y demos empresariales. El repositorio combina una capa documental fuerte con **10 casos operativos**: 01, 02, 03, 04, 05, 09, 10, 13, 19 y 25.

---

## Implementacion Industrial (v4.2.0)

El estandar actual del repositorio se apoya en estos pilares:

1. **Portal unificado**: `index.html` como entrada principal para navegar el portafolio.
2. **Casos de referencia reales**: backends FastAPI y UIs activas en los casos 01, 02, 03, 04, 05, 09, 10, 13, 19 y 25.
3. **Estado tipado**: contratos explicitos de estado con `TypedDict` y flujos compatibles con LangGraph.
4. **Observabilidad**: endpoints `/health`, `/ready` y `/metrics`, ademas de trazabilidad por eventos o `trace_id` segun el caso.
5. **Modo dual**: demos offline y ruta clara para activar integraciones reales mediante `.env.example`, `.env` y variables de entorno.
6. **Operacion portable**: ejecucion por Docker, Hub CLI o entorno local segun el caso.
7. **Hardening integrado**: workflows pinneados, baseline de secretos, auditoria de dependencias y control seguro del Hub CLI.
8. **Auth multicapa**: `X-Demo-Token` opt-in + OAuth2/OIDC JWT opt-in via `USE_OAUTH2=true`.

> [!TIP]
> Consulta el detalle tecnico en [CHANGELOG.md](CHANGELOG.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/TECHNICAL_SPECS.md](docs/TECHNICAL_SPECS.md), [docs/INSTALL.md](docs/INSTALL.md) y [SECURITY.md](SECURITY.md).

### Taxonomia de Implementacion

- **Operativo (v4.2.0)**: casos 01, 02, 03, 04, 05, 19 y 25 con backends reales, logicas condicionales robustas, modo DEMO/LIVE, UIs operativas e interactivas.
- **Industrial (v4.2.0)**: casos 09, 10 y 13 con backend real, streaming, estado tipado, observabilidad y documentacion operativa completa.
- **Scaffold**: demos o plantillas documentadas listas para elevar al siguiente nivel.

### Estado de los Casos Clave

| Case ID | Nombre | Estado | Stack principal |
| :--- | :--- | :--- | :--- |
| **01** | [Soporte Cliente Omnicanal](cases/01-soporte-cliente-omnicanal/README.md) | `OPERATIVO` | FastAPI + LangGraph + Routing + DEMO/LIVE |
| **02** | [Mesa de Ayuda TI](cases/02-mesa-ayuda-ti-runbooks/README.md) | `OPERATIVO` | FastAPI + CMDB + LangGraph + HITL |
| **03** | [Incident Response SRE](cases/03-incident-response-sre/README.md) | `OPERATIVO` | FastAPI + LangGraph + PagerDuty DEMO |
| **04** | [SOC Triage de Alertas](cases/04-soc-triage-alertas/README.md) | `OPERATIVO` | FastAPI + LangGraph + Router de riesgo + Threat Intel |
| **05** | [Analista de Documentos](cases/05-analista-documentos/README.md) | `OPERATIVO` | FastAPI + LangGraph + 7 nodos + Router condicional |
| **09** | [RRHH Screening Agenda](cases/09-rrhh-screening-agenda/README.md) | `INDUSTRIAL` | FastAPI + LangGraph + MemorySaver + Resilience |
| **10** | [Onboarding Empleados](cases/10-onboarding-empleados/README.md) | `INDUSTRIAL` | FastAPI + RBAC + Integrations + MemorySaver |
| **13** | [BI Data Analyst](cases/13-bi-analista-datos/README.md) | `INDUSTRIAL` | FastAPI + SQL Agent + Chart.js + DEMO/LLM |
| **19** | [DevEx: PR Review](cases/19-devex-pr-review/README.md) | `OPERATIVO` | FastAPI + LangGraph + GitHub API DEMO |
| **25** | [Supervisor + Workers](cases/25-supervisor-workers/README.md) | `OPERATIVO` | FastAPI + LangGraph + Multi-agent |

---

## Por donde empezar

| Perfil | Ruta recomendada | Que mirar |
| :--- | :--- | :--- |
| Dev / DevOps | [Caso 01](cases/01-soporte-cliente-omnicanal/README.md) | Triage omnicanal, routing y fallback DEMO/LIVE |
| IT Admin / SRE | [Caso 02](cases/02-mesa-ayuda-ti-runbooks/README.md) | Enriquecimiento de perfil, HITL, suite propia y control de exposicion |
| Seguridad | [Caso 04](cases/04-soc-triage-alertas/README.md) | SOC Triage, router de riesgo, threat intel |
| Legal / Contratos | [Caso 05](cases/05-analista-documentos/README.md) | Analisis de clausulas, clasificacion de riesgo, escalado |
| Dev / DevOps | [Caso 09](cases/09-rrhh-screening-agenda/README.md) | Resiliencia, streaming y activacion opcional de integraciones |
| Dev / DevOps | [Caso 10](cases/10-onboarding-empleados/README.md) | Flujo empresarial, RBAC e integraciones |
| Analista / BI | [Caso 13](cases/13-bi-analista-datos/README.md) | SQL seguro, visualizacion y activacion opcional de LLM |
| Recruiter / Hiring Manager | [docs/RECRUITER.md](docs/RECRUITER.md) | Resumen ejecutivo, senales de seniority y ruta de evaluacion |
| Principiante | [docs/BEGINNERS_GUIDE.md](docs/BEGINNERS_GUIDE.md) | Mapa del repositorio |
| Auditoria | [SECURITY.md](SECURITY.md) | Postura de hardening, manejo de secretos y limites reales |

---

## Activar APIs opcionales

- Copia `backend/.env.example` a `backend/.env` en el caso que quieras llevar a LIVE.
- O abre el portal raiz y usa `Configurar APIs del portfolio` para completar credenciales, ver donde obtenerlas y exportar el `.env` por caso.
- Si no agregas credenciales, los casos siguen funcionando en DEMO.

### Perfil de exposicion externa

Si un backend va a salir de `localhost`, activa controles adicionales en su `.env`:

```env
DEMO_AUTH_TOKEN=replace-with-a-long-random-token
RATE_LIMIT_RPM=60
TRUST_PROXY_HEADERS=false
```

Estos controles son opcionales y no se activan por defecto para no romper demos, quickstart ni navegacion local.

> [!IMPORTANT]
> El portal solo persiste valores si pulsas `Guardar localmente`, y los deja en `localStorage` del navegador en texto claro. Usalo solo en un equipo confiable. Para trabajo serio, inyecta secretos via `.env`, variables de entorno o un secret manager externo.
