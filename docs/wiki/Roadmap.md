# Hoja de Ruta

> **Version**: 4.5.0 | **Estado**: Industrial

El estandar tecnico del repositorio ya esta definido. Ver el [SKILL de creacion de casos](https://github.com/vladimiracunadev-create/langgraph-realworld/blob/main/.agents/skills/crear_caso/SKILL.md) antes de ejecutar cualquier tarea.

---

## Estado actual

13 casos operativos e industriales: 01, 02, 03, 04, 05, 08, 09, 10, 13, 14, 17, 19, 25.
12 casos scaffold listos para elevar.

---

## Orden de elevacion de casos

```
SCAFFOLD  →  (SKILL.md)  →  OPERATIVO  →  (observabilidad + hardening)  →  INDUSTRIAL
```

### Ola 1 — Alta prioridad

| Caso | Dominio | Estado |
|:---|:---|:---|
| ~~04 — SOC Triage~~ | Seguridad | **COMPLETADO v4.1.0** — Router de riesgo, threat intel, SIEM context |
| ~~05 — Analista de Documentos~~ | Legal / Contratos | **COMPLETADO v4.2.0** — 7 nodos, router de riesgo, 3 docs DEMO |
| ~~17 — Legal Intake~~ | Legal | **COMPLETADO v4.3.0** — Intake + 3 especialidades + 3 plantillas + asignacion de abogado |

### Ola 2 — Impacto comercial

| Caso | Dominio | Estado |
|:---|:---|:---|
| ~~08 — Ventas B2B + CRM~~ | Comercial | **COMPLETADO v4.4.0** — Pipeline outbound: ICP scoring, outreach por industria, CRM stage automatico |
| ~~14 — Finanzas: Conciliacion~~ | Finanzas | **COMPLETADO v4.5.0** — Matching multi-criterio, z-score outliers, indicador verde/amarillo/rojo |
| 06 — Compliance & Auditorias | Gobernanza | Pendiente |
| 21 — Documentacion Automatica | DevOps | Pendiente |

### Ola 3 — Dominio especializado

07, 11, 12, 15, 16, 18, 20, 22, 23, 24 — segun disponibilidad y demanda.

---

## Mejoras transversales pendientes

| Caso | Integracion pendiente |
|:---:|:---|
| 03 | PagerDuty + Datadog reales |
| 04 | VirusTotal + AbuseIPDB + Splunk/Elastic reales |
| 08 | HubSpot / Salesforce / Pipedrive reales (CRM API) |
| 10 | HRIS, IAM, Slack, correo (4 TODO REAL) |
| 14 | SAP / Oracle / Quickbooks reales (MT940 / CAMT.053) |
| 17 | LLM senior para redaccion legal (opt-in) |
| 19 | GitHub API real (GITHUB_TOKEN) |
| 25 | APIs financieras/legales reales |

Casos 03, 08, 14, 17, 19, 25 pendientes de elevacion a INDUSTRIAL: compose.smoke, logging JSON estructurado, /metrics documentado, OAuth2 verificado en tests.

---

## Largo plazo

- Kubernetes con NetworkPolicy y SecurityContext completos.
- IaC (Terraform / Pulumi) para entornos reproducibles en cloud.
- OpenTelemetry para trazas distribuidas entre servicios.
- Secret manager externo (Vault, AWS Secrets Manager).

---

Para el detalle completo con enlaces a todos los documentos, ver [ROADMAP.md en el repositorio](https://github.com/vladimiracunadev-create/langgraph-realworld/blob/main/ROADMAP.md).
