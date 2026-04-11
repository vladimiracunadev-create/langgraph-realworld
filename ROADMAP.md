# Hoja de Ruta

> [!NOTE]
> **Versión**: 4.0.1 | **Estado**: Industrial | **Audiencia**: Stakeholders, Colaboradores, Agentes automatizados

El estándar técnico del repositorio ya está definido. No se re-analiza en cada ciclo. Para crear o elevar un caso, seguir el SKILL directamente: [`.agents/skills/crear_caso/SKILL.md`](.agents/skills/crear_caso/SKILL.md).

---

## Estado actual

### Casos operativos e industriales (8)

| ID | Nombre | Nivel | Interfaz web | Integraciones LIVE |
|:---:|:---|:---:|:---:|:---|
| 01 | Soporte Cliente Omnicanal | `OPERATIVO` | ✅ | LLM (OpenAI opt-in) |
| 02 | Mesa de Ayuda TI / SRE | `OPERATIVO` | ✅ | CMDB, runbooks (DEMO) |
| 03 | Incident Response SRE | `OPERATIVO` | ✅ | PagerDuty, Datadog (DEMO) |
| 09 | RRHH Screening & Agenda | `INDUSTRIAL` | ✅ | LLM + MemorySaver |
| 10 | Onboarding de Empleados | `INDUSTRIAL` | ✅ | HRIS, IAM, Slack (DEMO) |
| 13 | Analista de Datos BI | `INDUSTRIAL` | ✅ | SQL + Chart.js + LLM opt-in |
| 19 | DevEx: PR Review | `OPERATIVO` | ✅ | GitHub API (DEMO) |
| 25 | Supervisor + Workers | `OPERATIVO` | ✅ | 4 workers especializados (DEMO) |

### Casos scaffold (17) — listos para elevar

| ID | Nombre | Dominio | Prioridad |
|:---:|:---|:---|:---:|
| 04 | SOC: Triage de Alertas | Seguridad / SOC | 🔴 Alta |
| 05 | Analista de Documentos | Legal / Contratos | 🔴 Alta |
| 17 | Legal Intake | Legal | 🔴 Alta |
| 08 | Ventas B2B + CRM | Comercial | 🟠 Media |
| 14 | Finanzas: Conciliación | Finanzas | 🟠 Media |
| 06 | Compliance & Auditorías | Gobernanza | 🟠 Media |
| 21 | Documentación Automática | DevOps | 🟠 Media |
| 22 | Backoffice: Automatización | Operaciones | 🟡 Normal |
| 24 | Asistente PM | Gestión de proyectos | 🟡 Normal |
| 15 | E-commerce Postventa | Comercio electrónico | 🟡 Normal |
| 07 | Compras y Abastecimiento | Procurement | 🟡 Normal |
| 11 | Tutor Adaptativo | Educación | 🟡 Normal |
| 12 | Psicometría y Evaluaciones | RRHH / Evaluación | 🟡 Normal |
| 18 | Marketing con QA | Marketing | 🟡 Normal |
| 20 | Migración Legacy | Arquitectura | 🟡 Normal |
| 23 | Salud: Pre-triage | Salud | 🟡 Normal |
| 16 | Planificador de Viajes | Travel | 🟡 Normal |

---

## Orden de elevación de casos

La elevación de un scaffold a OPERATIVO sigue siempre el mismo proceso. No se rediseña el proceso en cada ciclo: está en el SKILL.

```text
SCAFFOLD  →  (seguir SKILL.md)  →  OPERATIVO  →  (streaming + observabilidad + hardening)  →  INDUSTRIAL
```

### Ola 1 — Casos de alta prioridad (próximos a elevar)

Estos tres casos tienen dominio de alto impacto empresarial y sus scaffolds ya tienen README con Mermaid. Son los candidatos naturales para la siguiente ola.

| # | Caso | Razón de prioridad | LangGraph central |
|:---:|:---|:---|:---|
| 1 | **04 — SOC Triage** | Dominio de seguridad. Complementa el caso 03 (Incident Response). Alto valor en portfolios de AI+Sec. | Router por severidad, HITL, escalada automatizada |
| 2 | **05 — Analista de Documentos** | Caso de extracción y síntesis sobre PDFs/contratos. Patrón muy solicitado en enterprise. Bajo acoplamiento externo. | Pipeline secuencial, extracción estructurada, resumen LLM |
| 3 | **17 — Legal Intake** | Continuación natural del caso 05 en dominio legal. Intake + clasificación + routing a especialistas. | Clasificación + routing condicional, HITL para escalada |

### Ola 2 — Casos de impacto comercial y operativo

| # | Caso | Razón de prioridad |
|:---:|:---|:---|
| 4 | **08 — Ventas B2B + CRM** | CRM automation + lead scoring. Alta demanda de negocio. Integración con HubSpot/Salesforce en LIVE. |
| 5 | **14 — Finanzas: Conciliación** | Reconciliación automática de transacciones. Alto ROI claro. Patrón de verificación + excepción. |
| 6 | **06 — Compliance & Auditorías** | Gobernanza + generación de reportes. Complementa el hardening de seguridad del repo. |
| 7 | **21 — Documentación Automática** | DevOps docs generation. Relevante para el propio repo. Patrón de código → doc estructurada. |

### Ola 3 — Casos de dominio especializado

| # | Caso | Razón de prioridad |
|:---:|:---|:---|
| 8 | **22 — Backoffice Automatización** | Automatización de procesos repetitivos. Alta generalización. |
| 9 | **24 — Asistente PM** | Gestión de proyectos con LLM. Patrón de planning + tracking + reporting. |
| 10 | **15 — E-commerce Postventa** | Atención postventa automatizada. Complementa caso 01 (soporte). |
| 11 | **07 — Compras y Abastecimiento** | Procurement con aprobaciones. HITL natural. |
| 12-17 | Resto | Elevar según disponibilidad y demanda del portfolio. |

---

## Mejoras transversales pendientes

Estas mejoras no son casos nuevos sino mejoras al estándar de los casos existentes. Se priorizan cuando hay capacidad entre olas.

### v4.1.0 — Integraciones reales en casos operativos

| Caso | Integración pendiente | Requisito |
|:---:|:---|:---|
| 19 — PR Review | GitHub API real para modo LIVE | `GITHUB_TOKEN` configurado |
| 10 — Onboarding | HRIS, IAM, Slack, correo (4 `TODO REAL` en `integrations.py`) | Credenciales por `.env` |
| 03 — Incident Response | PagerDuty + Datadog reales | `PAGERDUTY_TOKEN`, `DATADOG_API_KEY` |
| 25 — Due Diligence | APIs financieras/legales reales | Por definir según caso de uso |

### Elevación a INDUSTRIAL (casos operativos actuales)

Los casos 03, 19 y 25 son OPERATIVO. Para llegar a INDUSTRIAL necesitan:

- [ ] `compose.smoke.yml` con smoke tests en Docker
- [ ] Tests de integración con `stream_mode` verificado
- [ ] `/metrics` documentado en su `README.md`
- [ ] Logging JSON estructurado con `ContextVar` + `TraceIdFilter` (como casos 09/10)
- [ ] OAuth2/OIDC opt-in verificado (ya tienen `auth.py`, confirmar en tests)

### Largo plazo

- Kubernetes con `NetworkPolicy` y `SecurityContext` completos.
- IaC (Terraform / Pulumi) para entornos reproducibles en cloud.
- OpenTelemetry para trazas distribuidas entre servicios (más allá de LangSmith).
- Secret manager externo (Vault, AWS Secrets Manager) para demos persistentes.

---

## Criterios de madurez

```text
SCAFFOLD   → README con Mermaid + case.yml + estructura de carpetas
               ↓  (seguir SKILL.md — el proceso ya está definido)
OPERATIVO  → backend real + interfaz web + DEMO/LIVE + Docker + tests básicos + docs
               ↓  (streaming + observabilidad + hardening completo)
INDUSTRIAL → OPERATIVO + compose.smoke + logging JSON + /metrics documentado
             + OAuth2 opt-in verificado + tests de streaming + docs operativas completas
```

---

## Referencias de estándar

El estándar del repositorio **ya está definido**. No se rediseña en cada ciclo. Consultar directamente:

| Documento | Qué define |
|:---|:---|
| [`.agents/skills/crear_caso/SKILL.md`](.agents/skills/crear_caso/SKILL.md) | Proceso completo de creación/elevación de un caso (contrato técnico, DEMO/LIVE, interfaz web, criterios de cierre) |
| [`docs/TECHNICAL_SPECS.md`](docs/TECHNICAL_SPECS.md) | Stack técnico, contratos de API, guardrails de seguridad |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Estructura del monorepo, patrón DEMO/LIVE, integración con compose y hub |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Reglas de código, estilo, testing y Docker |
| [`SECURITY.md`](SECURITY.md) | Postura de seguridad, 8 capas, riesgos aceptados |
