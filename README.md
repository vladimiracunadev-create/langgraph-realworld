<div align="center">

# 🤖 LangGraph Realworld

### **25 casos de uso empresariales · 25 backends operativos · 100% DEMO sin APIs**

**LangGraph · FastAPI · Python 3.11 · Docker · OAuth2 · LangSmith · uv (opcional)**

[![Version](https://img.shields.io/badge/version-4.14.0-1f6feb?style=for-the-badge)](CHANGELOG.md)
[![Operativos](https://img.shields.io/badge/operativos-25%2F25-3fb950?style=for-the-badge)](ROADMAP.md)
[![Tests](https://img.shields.io/badge/tests-passing-3fb950?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge)](LICENSE)

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1-FF6F00?style=flat-square&logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](docker-compose.yml)
[![uv](https://img.shields.io/badge/uv-opcional-7c3aed?style=flat-square&logo=astral&logoColor=white)](docs/UV.md)
[![CodeQL](https://img.shields.io/badge/CodeQL-enabled-2f81f7?style=flat-square&logo=github&logoColor=white)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/codeql.yml)
[![Security](https://img.shields.io/badge/security-8_capas-f87171?style=flat-square&logo=shield&logoColor=white)](SECURITY.md)
[![CI](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml)
[![Security Scan](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml)

</div>

> Portafolio de **25 casos de uso empresariales** construidos con **LangGraph** y **FastAPI**:
> **25 backends completamente operativos** (casos 01-25 sin omisiones) con streaming, OAuth2/OIDC opt-in, observabilidad LangSmith, `/metrics` por servicio, logging JSON estructurado y reverse proxy nginx + TLS.
> Ola 3 cerrada en v4.14.0 — portfolio al 100%.

### 📊 Estado del portfolio

| 🎯 | Métrica | Valor |
|:-:|:---|:---|
| 🟢 | Casos operativos | **25 / 25** (100%) |
| 🏭 | Casos industriales | **3** (09, 10, 13) |
| 📋 | Scaffolds restantes | **0** (Ola 3 cerrada) |
| 🧪 | Tests por caso | 18-30, todos verdes |
| 🔌 | Modo DEMO | 100% sin APIs externas |
| 🔑 | Modo LIVE | Opt-in con `OPENAI_API_KEY` |
| 🛡️ | Auditoría seguridad | 8 capas (`SECURITY.md`) |
| ⚡ | Tooling | `pip` + `pip-tools` (defecto), `uv` (~10× opcional) |

### 🔥 Casos destacados

| Caso | Tag | Por qué mirarlo |
|:-:|:---|:---|
| **04** | 🛡️ SOC | Router de riesgo (3 vías), threat intel, SIEM context |
| **06** | 🛡️ Compliance | ISO/SOC2/GDPR + cadena de custodia SHA-256 encadenada |
| **07** | 🛒 Compras | Score multi-criterio (precio/plazo/riesgo) + router política comité + OC con SHA-256 |
| **13** | 📊 BI | SQL agent endurecido + Chart.js + LLM opt-in |
| **14** | 💰 Finanzas | Matching multi-criterio + z-score outliers determinista |
| **17** | ⚖️ Legal | 3 especialidades + 3 plantillas + asignación de abogado |
| **18** | 📣 Marketing | Doble loop QA: estilo de marca + fact-check con fuentes |
| **22** | 🏢 Backoffice | 3 routers + loop completitud + log inmutable SHA-256 |
| **21** | 📝 Docs | Loop QA condicional (tope 3 iter) + outline adaptativo |
| **25** | 🤝 Multi-agent | Supervisor + 4 workers especializados (DEMO) |

---

## 🏗️ Implementación Industrial — v4.14.0

El estándar actual del repositorio se apoya en estos pilares:

| # | Pilar | Descripción |
|:-:|:---|:---|
| 1 | 🌐 **Portal unificado** | `index.html` como entrada principal para navegar el portafolio |
| 2 | ⚙️ **Casos de referencia reales** | Backends FastAPI y UIs activas en los casos 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 13, 14, 17, 18, 19, 21, 22 y 25 |
| 3 | 📐 **Estado tipado** | Contratos explícitos con `TypedDict` y flujos compatibles con LangGraph |
| 4 | 🔭 **Observabilidad** | `/health`, `/ready`, `/metrics` con latencia, errores y modo; LangSmith opt-in |
| 5 | 🔀 **Modo dual** | Demos offline + ruta clara para activar integraciones reales |
| 6 | 🐳 **Operación portable** | Docker, nginx+TLS, Hub CLI o entorno local según el caso |
| 7 | 🛡️ **Hardening integrado** | grype `fail-build:true`, detect-secrets history, pip-compile, Dependabot |
| 8 | 🔑 **Auth multicapa** | `X-Demo-Token` (opt-in) + OAuth2/OIDC JWT (opt-in via `USE_OAUTH2=true`) |
| 9 | 🔒 **Auditoría de seguridad 8 capas** | Non-root, `127.0.0.1`, HTTP headers, grype, Trojan Source, nginx TLS |

> [!TIP]
> Consulta el detalle técnico en [CHANGELOG.md](CHANGELOG.md), [SECURITY.md](SECURITY.md) y los docs en [`docs/`](docs/).

---

## 📦 Estado de los casos

### ✅ Casos operativos e industriales

| ID | Nombre | Estado | Stack principal |
|:---:|:---|:---:|:---|
| **01** | [🎧 Soporte Cliente Omnicanal](cases/01-soporte-cliente-omnicanal/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · Routing · OAuth2 opt-in |
| **02** | [🖥️ Mesa de Ayuda TI / SRE](cases/02-mesa-ayuda-ti-runbooks/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · CMDB · HITL |
| **03** | [🚨 Incident Response SRE](cases/03-incident-response-sre/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · HITL · Runbooks P1/P2/P3 |
| **04** | [🔐 SOC Triage de Alertas](cases/04-soc-triage-alertas/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · Threat Intel · Router de riesgo |
| **05** | [📄 Analista de Documentos](cases/05-analista-documentos/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · Keyword extraction · Router de riesgo |
| **06** | [🛡️ Compliance & Auditorías](cases/06-compliance-auditorias/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · ISO/SOC/GDPR · Cadena de custodia SHA-256 |
| **07** | [🛒 Compras y Abastecimiento](cases/07-compras-abastecimiento/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · Score multi-criterio · Router política comité · OC SHA-256 |
| **08** | [💼 Ventas B2B + CRM](cases/08-ventas-b2b-crm/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · ICP scoring · CRM stage automático |
| **09** | [👥 RRHH Screening & Agenda](cases/09-rrhh-screening-agenda/README.md) | `🏭 INDUSTRIAL` | FastAPI · LangGraph · MemorySaver · Resilience |
| **10** | [🚀 Onboarding de Empleados](cases/10-onboarding-empleados/README.md) | `🏭 INDUSTRIAL` | FastAPI · LangGraph · RBAC · Integrations |
| **11** | [🎓 Tutor Adaptativo](cases/11-educacion-tutor-adaptativo/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · Simulador IRT · 3 routers · Loop adaptativo |
| **12** | [🧠 Psicometría y Evaluaciones](cases/12-psicometria-evaluaciones/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · α Cronbach · Discriminación · DIF · Loop validez |
| **13** | [📊 Analista de Datos BI](cases/13-bi-analista-datos/README.md) | `🏭 INDUSTRIAL` | FastAPI · SQL Agent · Chart.js · DEMO/LLM |
| **14** | [💰 Finanzas — Conciliación](cases/14-finanzas-conciliacion/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · matching multi-criterio · z-score outliers |
| **15** | [🛍️ E-commerce Postventa](cases/15-ecommerce-postventa/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · 3 routers · Etiqueta SHA-256 · Convergencia humano |
| **16** | [✈️ Planificador de Viajes](cases/16-viajes-planificador/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · Itinerario multi-criterio · Travel DEMO |
| **17** | [⚖️ Legal Intake](cases/17-legal-intake/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · 3 especialidades · 3 plantillas · Asignación |
| **18** | [📣 Marketing con QA](cases/18-marketing-contenido-qa/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · Doble loop QA · Brand guard · Fact-check |
| **19** | [🔍 DevEx: PR Review](cases/19-devex-pr-review/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · Security Analysis · Changelog |
| **20** | [🏛️ Migración Legacy](cases/20-migracion-legacy/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · Inventario · Plan de migración multi-fase |
| **21** | [📝 Documentación Automática](cases/21-docs-auto/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · Outline adaptativo · Loop QA condicional |
| **22** | [🏢 Backoffice Automatización](cases/22-backoffice-automatizacion/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · 3 routers · Loop completitud · Cadena SHA-256 |
| **23** | [🏥 Salud: Pre-triage](cases/23-salud-pretriage/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · Triage clínico · Routers de severidad |
| **24** | [📋 Asistente PM](cases/24-pm-assistant/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · Backlog · Riesgos · Reportes ejecutivos |
| **25** | [🤝 Supervisor + Workers](cases/25-supervisor-workers/README.md) | `✅ OPERATIVO` | FastAPI · LangGraph · Multi-agente · Due Diligence |

> Ola 3 cerrada en v4.14.0 — los 25 casos están operativos. No quedan scaffolds pendientes.

---

## 🧭 Por dónde empezar

| Perfil | Ruta recomendada | Qué explorar |
|:---|:---|:---|
| 👨‍💻 Dev / DevOps | [Caso 01](cases/01-soporte-cliente-omnicanal/README.md) | Routing condicional y fallback DEMO/LIVE |
| 🖥️ IT Admin / SRE | [Caso 02](cases/02-mesa-ayuda-ti-runbooks/README.md) | Enriquecimiento de perfil, HITL y runbooks |
| 🤖 Dev / ML Eng | [Caso 09](cases/09-rrhh-screening-agenda/README.md) | Resiliencia, streaming y MemorySaver |
| 🏗️ Dev / Arquitecto | [Caso 10](cases/10-onboarding-empleados/README.md) | RBAC, flujo empresarial e integraciones |
| 📊 Analista / BI | [Caso 13](cases/13-bi-analista-datos/README.md) | SQL seguro, visualización y LLM opcional |
| 🧑‍💼 Recruiter / HM | [docs/RECRUITER.md](docs/RECRUITER.md) | Resumen ejecutivo y señales de seniority |
| 🐣 Principiante | [docs/BEGINNERS_GUIDE.md](docs/BEGINNERS_GUIDE.md) | Mapa del repositorio paso a paso |
| 🔒 Auditor / CISO | [SECURITY.md](SECURITY.md) | Postura de seguridad, controles y riesgos aceptados |

---

## 📚 Documentación completa

### Visión y estrategia

| Documento | Contenido |
|:---|:---|
| [ROADMAP.md](ROADMAP.md) | Hoja de ruta — mapa de todos los documentos, estado de los 25 casos, orden de elevación por olas, mejoras transversales |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios por versión |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Cómo contribuir — estructura, estilo, testing y Docker |
| [SECURITY.md](SECURITY.md) | Auditoría 8 capas, riesgos aceptados, hardening |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Código de conducta |
| [killed.md](killed.md) | Features eliminadas o pausadas |

### Técnica

| Documento | Contenido |
|:---|:---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Estructura del monorepo, patrón DEMO/LIVE, compose y hub |
| [docs/TECHNICAL_SPECS.md](docs/TECHNICAL_SPECS.md) | Stack, contratos de API, guardrails de seguridad |
| [docs/INSTALL.md](docs/INSTALL.md) | Cómo levantar el repo: Docker, local, Hub CLI, uv opt-in |
| [docs/UV.md](docs/UV.md) | ⚡ Uso opcional de `uv` (Astral) — gestor Python ~10× más rápido que pip |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Requisitos: Git, Python, Docker, APIs opcionales |
| [docs/HUB.md](docs/HUB.md) | Hub CLI — comandos, guardrails, estado de casos |
| [docs/AGENTS_AND_SKILLS.md](docs/AGENTS_AND_SKILLS.md) | Skills de agentes, estándar de un caso completo, orden de trabajo |
| [docs/CLOUD_AWS.md](docs/CLOUD_AWS.md) | ☁️ Migración a AWS — 3 estrategias (PoC ~25 USD · Producción ~180 USD · Enterprise ~650 USD), mapeo Docker→AWS, paso a paso, costos y FinOps |
| [docs/COSTS.md](docs/COSTS.md) | 💰 Costos DEMO vs LIVE — APIs requeridas por caso, pricing público OpenAI/SaaS, recetas para activar LIVE |

### Wiki (publicada en GitHub)

La wiki contiene versiones navegables de la documentación técnica publicadas automáticamente desde `docs/wiki/` en cada push a `main`.

| Página | Contenido |
|:---|:---|
| [Wiki Home](https://github.com/vladimiracunadev-create/langgraph-realworld/wiki) | Entrada de la wiki — estado del portfolio, inicio rápido |
| [Roadmap](https://github.com/vladimiracunadev-create/langgraph-realworld/wiki/Roadmap) | Hoja de ruta — orden de elevación de casos, mejoras pendientes |
| [Arquitectura](https://github.com/vladimiracunadev-create/langgraph-realworld/wiki/Arquitectura) | Estructura del monorepo y patrón DEMO/LIVE |
| [Especificaciones Técnicas](https://github.com/vladimiracunadev-create/langgraph-realworld/wiki/Especificaciones-Tecnicas) | Stack, contratos de API, guardrails |
| [Seguridad](https://github.com/vladimiracunadev-create/langgraph-realworld/wiki/Security) | Auditoría 8 capas |
| [Guía para Principiantes](https://github.com/vladimiracunadev-create/langgraph-realworld/wiki/Guia-para-Principiantes) | Mapa del repo paso a paso |
| [Hub CLI](https://github.com/vladimiracunadev-create/langgraph-realworld/wiki/Hub-CLI) | Comandos del Hub CLI |

---

## ⚡ Inicio rápido

```bash
# 1. Clonar
git clone https://github.com/vladimiracunadev-create/langgraph-realworld.git
cd langgraph-realworld

# 2. Copiar credenciales (opcional — los casos funcionan en DEMO sin ellas)
cp .env.example .env
# Editar .env con tu OPENAI_API_KEY

# 3. Levantar un caso con Docker
docker compose up case01
# → UI disponible en http://localhost:8001/web/

# 4. O usar el Hub CLI
python hub.py list
python hub.py run --case 01
```

> [!IMPORTANT]
> Los casos funcionan en **DEMO** sin credenciales externas. Agrega `OPENAI_API_KEY` en `.env` para activar el modo **LIVE** con integraciones reales.

---

## 🔑 Activar APIs opcionales

- Copia `backend/.env.example` a `backend/.env` en el caso que quieras llevar a LIVE.
- O abre el portal raíz y usa **Configurar APIs del portfolio** para exportar el `.env` por caso.
- Sin credenciales, todos los casos funcionan en **DEMO** automáticamente.

### 🌐 Perfil de exposición externa

Si un backend va a salir de `localhost`, activa controles adicionales en su `.env`:

```env
DEMO_AUTH_TOKEN=replace-with-a-long-random-token
RATE_LIMIT_RPM=60
TRUST_PROXY_HEADERS=false
```

> [!IMPORTANT]
> El portal sólo persiste valores si pulsas **Guardar localmente**. Los almacena en `localStorage` del navegador en texto claro. Úsalo sólo en equipos de confianza. Para trabajo serio, inyecta secretos vía `.env`, variables de entorno o un secret manager externo.

---

## 📐 Taxonomía de implementación

| Nivel | Criterios | Casos |
|:---|:---|:---|
| ✅ **OPERATIVO** | Backend real, DEMO/LIVE, CI, tests, hardening, OAuth2 opt-in | 01, 02, 03, 04, 05, 06, 07, 08, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 |
| 🏭 **INDUSTRIAL** | Backend real, streaming, observabilidad, docs completas | 09, 10, 13 |
| 🔧 **SCAFFOLD** | Demo estática lista para evolucionar | — (ninguno: Ola 3 cerrada en v4.14.0) |

---

## 🛡️ Seguridad

Este repositorio ha sido auditado por **8 capas de seguridad** (v4.14.0):

| Capa | Control | Estado |
|:---|:---|:---:|
| 🐳 Contenedores | Usuario non-root (`appuser`/`nginx`), imágenes pineadas | ✅ |
| 🌐 Red | Puertos vinculados a `127.0.0.1` | ✅ |
| 🔒 Credenciales | `detect-secrets` + baseline enforced en CI | ✅ |
| 🛡️ Web server | HTTP security headers en los 25 demos nginx | ✅ |
| 🔍 Dependencias | `pip-audit` + Dependabot semanal | ✅ |
| 🧪 SAST | CodeQL analysis en Python | ✅ |
| 🏗️ CI/CD | Actions pinneadas a SHA, sin `persist-credentials` | ✅ |
| ⛓️ Supply chain | grype scan, detección Trojan Source (CVE-2021-42574) | ✅ |

Consulta [SECURITY.md](SECURITY.md) para el detalle completo, riesgos aceptados y roadmap de hardening.
