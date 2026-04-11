# Hoja de Ruta

> **Versión**: 4.0.1 | **Estado**: Industrial | **Rama principal**: `main`

El estándar técnico del repositorio ya está definido. Los agentes y colaboradores deben leer el skill correspondiente antes de ejecutar cualquier tarea — no se rediseña lo ya definido.

---

## Mapa de documentación

### Raíz

| Documento | Propósito |
|:---|:---|
| [README.md](README.md) | Entrada principal del portfolio — estado de casos, inicio rápido, taxonomía |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios por versión |
| [ROADMAP.md](ROADMAP.md) | Este documento — visión estratégica y orden de trabajo |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Reglas de código, estilo, testing y Docker para colaboradores |
| [SECURITY.md](SECURITY.md) | Postura de seguridad, auditoría 8 capas, riesgos aceptados |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Código de conducta del proyecto |
| [killed.md](killed.md) | Features eliminadas o pausadas con su razón |

### Documentación técnica (`docs/`)

| Documento | Propósito |
|:---|:---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Estructura del monorepo, patrón DEMO/LIVE, integración compose y hub |
| [docs/TECHNICAL_SPECS.md](docs/TECHNICAL_SPECS.md) | Stack técnico, contratos de API, guardrails de seguridad |
| [docs/AGENTS_AND_SKILLS.md](docs/AGENTS_AND_SKILLS.md) | Skills disponibles, estándar de un caso completo, orden de trabajo para agentes |
| [docs/INSTALL.md](docs/INSTALL.md) | Cómo levantar el repo: Docker, local, Hub CLI |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Requisitos de entorno: Git, Python, Docker, APIs opcionales |
| [docs/HUB.md](docs/HUB.md) | Hub CLI — comandos, guardrails, estado de casos |
| [docs/BEGINNERS_GUIDE.md](docs/BEGINNERS_GUIDE.md) | Mapa del repo paso a paso para nuevos usuarios |
| [docs/RECRUITER.md](docs/RECRUITER.md) | Resumen ejecutivo del portfolio para recruiters y tech leads |

### Skills de agentes (`.agents/`)

| Documento | Propósito |
|:---|:---|
| [.agents/skills/crear_caso/SKILL.md](.agents/skills/crear_caso/SKILL.md) | Crear o elevar un caso — contrato técnico completo, estándar de UI, DEMO/LIVE |
| [.agents/skills/actualizar_doc/SKILL.md](.agents/skills/actualizar_doc/SKILL.md) | Sincronizar README, docs y wiki cuando cambia el código |
| [.agents/skills/validar_caso/SKILL.md](.agents/skills/validar_caso/SKILL.md) | Auditar un caso existente — Docker, CI, DEMO/LIVE, hub, seguridad, docs |

---

## Estado de los 25 casos

### Operativos e industriales (8)

| ID | README | Nivel | UI web | Integraciones LIVE disponibles |
|:---:|:---|:---:|:---:|:---|
| 01 | [Soporte Cliente Omnicanal](cases/01-soporte-cliente-omnicanal/README.md) | OPERATIVO | ✅ | LLM opt-in (OpenAI) |
| 02 | [Mesa de Ayuda TI / SRE](cases/02-mesa-ayuda-ti-runbooks/README.md) | OPERATIVO | ✅ | CMDB, runbooks (DEMO) |
| 03 | [Incident Response SRE](cases/03-incident-response-sre/README.md) | OPERATIVO | ✅ | PagerDuty, Datadog (DEMO) |
| 09 | [RRHH Screening & Agenda](cases/09-rrhh-screening-agenda/README.md) | INDUSTRIAL | ✅ | LLM + MemorySaver |
| 10 | [Onboarding de Empleados](cases/10-onboarding-empleados/README.md) | INDUSTRIAL | ✅ | HRIS, IAM, Slack (DEMO) |
| 13 | [Analista de Datos BI](cases/13-bi-analista-datos/README.md) | INDUSTRIAL | ✅ | SQL + Chart.js + LLM opt-in |
| 19 | [DevEx: PR Review](cases/19-devex-pr-review/README.md) | OPERATIVO | ✅ | GitHub API (DEMO) |
| 25 | [Supervisor + Workers](cases/25-supervisor-workers/README.md) | OPERATIVO | ✅ | 4 workers especializados (DEMO) |

### Scaffold — listos para elevar (17)

| ID | README | Dominio | Prioridad de elevación |
|:---:|:---|:---|:---:|
| 04 | [SOC: Triage de Alertas](cases/04-soc-triage-alertas/README.md) | Seguridad / SOC | 🔴 Ola 1 |
| 05 | [Analista de Documentos](cases/05-analista-documentos/README.md) | Legal / Contratos | 🔴 Ola 1 |
| 17 | [Legal Intake](cases/17-legal-intake/README.md) | Legal | 🔴 Ola 1 |
| 08 | [Ventas B2B + CRM](cases/08-ventas-b2b-crm/README.md) | Comercial | 🟠 Ola 2 |
| 14 | [Finanzas: Conciliación](cases/14-finanzas-conciliacion/README.md) | Finanzas | 🟠 Ola 2 |
| 06 | [Compliance & Auditorías](cases/06-compliance-auditorias/README.md) | Gobernanza | 🟠 Ola 2 |
| 21 | [Documentación Automática](cases/21-docs-auto/README.md) | DevOps | 🟠 Ola 2 |
| 07 | [Compras y Abastecimiento](cases/07-compras-abastecimiento/README.md) | Procurement | 🟡 Ola 3 |
| 11 | [Tutor Adaptativo](cases/11-educacion-tutor-adaptativo/README.md) | Educación | 🟡 Ola 3 |
| 12 | [Psicometría y Evaluaciones](cases/12-psicometria-evaluaciones/README.md) | RRHH / Evaluación | 🟡 Ola 3 |
| 15 | [E-commerce Postventa](cases/15-ecommerce-postventa/README.md) | Comercio electrónico | 🟡 Ola 3 |
| 18 | [Marketing con QA](cases/18-marketing-contenido-qa/README.md) | Marketing | 🟡 Ola 3 |
| 22 | [Backoffice: Automatización](cases/22-backoffice-automatizacion/README.md) | Operaciones | 🟡 Ola 3 |
| 24 | [Asistente PM](cases/24-pm-assistant/README.md) | Gestión de proyectos | 🟡 Ola 3 |
| 16 | [Planificador de Viajes](cases/16-viajes-planificador/README.md) | Travel | 🟡 Ola 3 |
| 20 | [Migración Legacy](cases/20-migracion-legacy/README.md) | Arquitectura | 🟡 Ola 3 |
| 23 | [Salud: Pre-triage](cases/23-salud-pretriage/README.md) | Salud | 🟡 Ola 3 |

---

## Orden de elevación de casos

Elevar un caso de SCAFFOLD a OPERATIVO sigue siempre el mismo proceso. Está definido en el skill — no se reinventa:

> **Leer [`.agents/skills/crear_caso/SKILL.md`](.agents/skills/crear_caso/SKILL.md) antes de tocar código.**

```
SCAFFOLD  →  (SKILL.md)  →  OPERATIVO  →  (streaming + observabilidad + hardening)  →  INDUSTRIAL
```

### Ola 1 — Alta prioridad

| Caso | Por qué primero | Núcleo LangGraph |
|:---|:---|:---|
| **04 — SOC Triage** | Complementa caso 03 (Incident Response). Alto valor en portfolios AI+Seguridad. | Router por severidad, HITL, escalada |
| **05 — Analista de Documentos** | Patrón de extracción sobre PDFs muy demandado en enterprise. Bajo acoplamiento externo. | Pipeline secuencial, extracción estructurada, resumen LLM |
| **17 — Legal Intake** | Continuación natural del 05 en dominio legal. Intake + clasificación + routing a especialistas. | Router condicional, HITL para escalada |

### Ola 2 — Impacto comercial y operativo

| Caso | Por qué |
|:---|:---|
| **08 — Ventas B2B + CRM** | Lead scoring + CRM automation. Alta demanda. Integra con HubSpot/Salesforce en LIVE. |
| **14 — Finanzas: Conciliación** | Reconciliación de transacciones. ROI claro. Patrón verificación + excepción. |
| **06 — Compliance** | Gobernanza + reportes. Complementa el hardening de seguridad del repo. |
| **21 — Docs Automática** | Código → documentación estructurada. Relevante para el propio repo. |

### Ola 3 — Dominio especializado

Elevar según disponibilidad y demanda: 07, 11, 12, 15, 18, 22, 24, 16, 20, 23.

---

## Mejoras transversales pendientes

### v4.1.0 — Integraciones reales en casos operativos

| Caso | Integración pendiente | Variable de entorno |
|:---:|:---|:---|
| [03](cases/03-incident-response-sre/README.md) | PagerDuty + Datadog reales | `PAGERDUTY_TOKEN`, `DATADOG_API_KEY` |
| [10](cases/10-onboarding-empleados/README.md) | HRIS, IAM, Slack, correo (4 `TODO REAL`) | Por `.env` del caso |
| [19](cases/19-devex-pr-review/README.md) | GitHub API real | `GITHUB_TOKEN` |
| [25](cases/25-supervisor-workers/README.md) | APIs financieras/legales reales | Por definir |

### Elevación OPERATIVO → INDUSTRIAL (casos 03, 19, 25)

- [ ] `compose.smoke.yml` con smoke tests en Docker
- [ ] Tests de integración con `stream_mode` verificado
- [ ] Logging JSON estructurado con `ContextVar` + `TraceIdFilter` (como casos 09/10)
- [ ] OAuth2/OIDC opt-in confirmado en tests
- [ ] `/metrics` documentado en README del caso

### Largo plazo

- Kubernetes con `NetworkPolicy` y `SecurityContext` completos
- IaC (Terraform / Pulumi) para entornos reproducibles en cloud
- OpenTelemetry para trazas distribuidas entre servicios
- Secret manager externo (Vault, AWS Secrets Manager)

---

## Criterios de madurez

```
SCAFFOLD   → README con Mermaid + case.yml + estructura de carpetas base
                 ↓  seguir SKILL.md — el proceso ya está definido
OPERATIVO  → backend real + interfaz web + DEMO/LIVE + Docker + tests + docs
                 ↓  streaming verificado + observabilidad + hardening
INDUSTRIAL → todo lo de OPERATIVO + compose.smoke + logging JSON estructurado
             + /metrics documentado + OAuth2 verificado en tests + docs operativas completas
```
