# Hoja de Ruta

> **Versión**: 4.2.0 | **Estado**: Industrial | **Rama principal**: `main`

El estándar técnico del repositorio ya está definido. Antes de crear o modificar un caso, leer el skill directamente — no se rediseña lo que ya existe:

- Crear / elevar un caso → [`.agents/skills/crear_caso/SKILL.md`](.agents/skills/crear_caso/SKILL.md)
- Actualizar documentación → [`.agents/skills/actualizar_doc/SKILL.md`](.agents/skills/actualizar_doc/SKILL.md)
- Auditar un caso existente → [`.agents/skills/validar_caso/SKILL.md`](.agents/skills/validar_caso/SKILL.md)

---

## Estado de los 25 casos

### Operativos e industriales (10)

| ID | Caso | Nivel | UI web | Integraciones LIVE |
|:---:|:---|:---:|:---:|:---|
| 01 | [Soporte Cliente Omnicanal](cases/01-soporte-cliente-omnicanal/README.md) | OPERATIVO | ✅ | LLM opt-in (OpenAI) |
| 02 | [Mesa de Ayuda TI / SRE](cases/02-mesa-ayuda-ti-runbooks/README.md) | OPERATIVO | ✅ | CMDB, runbooks (DEMO) |
| 03 | [Incident Response SRE](cases/03-incident-response-sre/README.md) | OPERATIVO | ✅ | PagerDuty, Datadog (DEMO) |
| 04 | [SOC Triage de Alertas](cases/04-soc-triage-alertas/README.md) | OPERATIVO | ✅ | VirusTotal, AbuseIPDB, SIEM (DEMO) |
| 05 | [Analista de Documentos](cases/05-analista-documentos/README.md) | OPERATIVO | ✅ | PDF/DOCX opt-in, LLM opt-in (OpenAI) |
| 09 | [RRHH Screening & Agenda](cases/09-rrhh-screening-agenda/README.md) | INDUSTRIAL | ✅ | LLM + MemorySaver |
| 10 | [Onboarding de Empleados](cases/10-onboarding-empleados/README.md) | INDUSTRIAL | ✅ | HRIS, IAM, Slack (DEMO) |
| 13 | [Analista de Datos BI](cases/13-bi-analista-datos/README.md) | INDUSTRIAL | ✅ | SQL + Chart.js + LLM opt-in |
| 19 | [DevEx: PR Review](cases/19-devex-pr-review/README.md) | OPERATIVO | ✅ | GitHub API (DEMO) |
| 25 | [Supervisor + Workers](cases/25-supervisor-workers/README.md) | OPERATIVO | ✅ | 4 workers especializados (DEMO) |

### Scaffold — listos para elevar (15)

| ID | Caso | Dominio | Prioridad |
|:---:|:---|:---|:---:|
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

```
SCAFFOLD  →  (seguir SKILL.md)  →  OPERATIVO  →  (observabilidad + hardening)  →  INDUSTRIAL
```

### Ola 1 — Alta prioridad

| Caso | Por qué | Núcleo LangGraph |
|:---|:---|:---|
| ~~**04 — SOC Triage**~~ | ✅ **COMPLETADO v4.1.0** — Router de riesgo (3 vías), threat intel, SIEM context | Router por score, 2 routers condicionales, stubs LIVE |
| ~~**05 — Analista de Documentos**~~ | ✅ **COMPLETADO v4.2.0** — Pipeline contractual, 7 nodos, router de riesgo, 3 docs DEMO | Pipeline secuencial, router condicional, keyword extraction, LLM opt-in |
| **17 — Legal Intake** | Continuación natural del 05. Intake + clasificación + routing a especialistas. | Router condicional, HITL para escalada |

### Ola 2 — Impacto comercial

| Caso | Por qué |
|:---|:---|
| **08 — Ventas B2B + CRM** | Lead scoring + CRM automation. Integra con HubSpot/Salesforce en LIVE. |
| **14 — Finanzas: Conciliación** | Reconciliación de transacciones. ROI claro. Patrón verificación + excepción. |
| **06 — Compliance** | Gobernanza + reportes. Complementa el hardening de seguridad del repo. |
| **21 — Docs Automática** | Código → documentación estructurada. Relevante para el propio repo. |

### Ola 3 — Dominio especializado

Elevar según disponibilidad y demanda: 07, 11, 12, 15, 18, 22, 24, 16, 20, 23.

---

## Mejoras transversales pendientes

### v4.1.0 — SOC Triage operativo + integraciones reales

**Completado**: Caso 04 elevado a OPERATIVO — 8 nodos, 2 routers, stubs VirusTotal/SIEM/Ticketing.

**Integraciones reales pendientes en casos existentes**:

| Caso | Integración pendiente | Variable de entorno |
|:---:|:---|:---|
| [03](cases/03-incident-response-sre/README.md) | PagerDuty + Datadog reales | `PAGERDUTY_TOKEN`, `DATADOG_API_KEY` |
| [04](cases/04-soc-triage-alertas/README.md) | VirusTotal + AbuseIPDB + Splunk/Elastic reales | `VIRUSTOTAL_API_KEY`, `SPLUNK_TOKEN` |
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
                 ↓  seguir .agents/skills/crear_caso/SKILL.md
OPERATIVO  → backend real + interfaz web + DEMO/LIVE + Docker + tests + docs
                 ↓  streaming verificado + observabilidad + hardening completo
INDUSTRIAL → todo lo de OPERATIVO + compose.smoke + logging JSON estructurado
             + /metrics documentado + OAuth2 verificado en tests + docs operativas completas
```
