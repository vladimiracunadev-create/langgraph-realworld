# Hoja de Ruta

> **Version**: 4.15.0 | **Estado**: Industrial

El estandar tecnico del repositorio ya esta definido. Ver el [SKILL de creacion de casos](https://github.com/vladimiracunadev-create/langgraph-realworld/blob/main/.agents/skills/crear_caso/SKILL.md) antes de ejecutar cualquier tarea.

---

## Estado actual

25 casos operativos e industriales: 01-25 sin omisiones (Ola 3 cerrada en v4.14.0).
0 casos scaffold — portfolio al 100%.

**v4.15.0**: release de hardening de seguridad y mantenibilidad (auditoria adversarial v4.14.0). 4 critical fixes inline (PR #63), CI expandido a 25 casos (PR #64), `shared/lgrw_common/` como fuente canonica (PR #65), migracion `python-jose` → `joserfc` (PR #66). Ver [Changelog](Changelog) y [Security](Security).

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
| ~~06 — Compliance & Auditorias~~ | Gobernanza | **COMPLETADO v4.6.0** — Mapeo de controles ISO 27001/SOC 2/GDPR, recopilacion, escalacion, validacion y cadena de custodia SHA-256 encadenada |
| ~~21 — Documentacion Automatica~~ | DevOps | **COMPLETADO v4.7.0** — Pipeline LangGraph con loop QA condicional (tope 3 iter), outline adaptativo, score por seccion, publicacion Markdown |

### Ola 3 — Dominio especializado

| Caso | Dominio | Estado |
|:---|:---|:---|
| ~~07 — Compras y Abastecimiento~~ | Procurement | **COMPLETADO v4.8.0** — Score multi-criterio, router politica comite, OC SHA-256 |
| ~~11 — Tutor Adaptativo~~ | Educacion | **COMPLETADO v4.9.0** — IRT, router 3 vias, loop adaptativo, banco 15 items |
| ~~15 — E-commerce Postventa~~ | Retail | **COMPLETADO v4.10.0** — 3 routers (intencion/elegibilidad/stock), etiqueta SHA-256 |
| ~~12 — Psicometria y Evaluaciones~~ | RRHH | **COMPLETADO v4.11.0** — alpha Cronbach, DIF, loop validez, 3 instrumentos DEMO |
| ~~18 — Marketing con QA~~ | Marketing | **COMPLETADO v4.12.0** — Doble loop QA (estilo + hechos), fact-check con 6 fuentes |
| ~~22 — Backoffice Automatizacion~~ | Operaciones | **COMPLETADO v4.13.0** — 3 routers + loop completitud + cadena custodia SHA-256 |
| ~~16 — Planificador de Viajes~~ | Travel | **COMPLETADO v4.14.0** — Itinerario multi-criterio (precio · duración · calificación), puerto 8016 |
| ~~20 — Migracion Legacy~~ | Arquitectura | **COMPLETADO v4.14.0** — Inventario + dependencias + plan multi-fase + estimación de riesgo, puerto 8020 |
| ~~23 — Salud Pre-triage~~ | Salud | **COMPLETADO v4.14.0** — Triage clínico determinista + routers de severidad + disclaimer médico, puerto 8023 |
| ~~24 — Asistente PM~~ | Gestión de proyectos | **COMPLETADO v4.14.0** — Backlog + riesgos + priorización multi-criterio + reporte ejecutivo, puerto 8024 |

Ola 3 cerrada en v4.14.0 — portfolio al 100% (25/25 operativos).

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
