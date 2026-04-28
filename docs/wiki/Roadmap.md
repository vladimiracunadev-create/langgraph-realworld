# Hoja de Ruta

> **Version**: 4.2.0 | **Estado**: Industrial

El estandar tecnico del repositorio ya esta definido. Ver el [SKILL de creacion de casos](https://github.com/vladimiracunadev-create/langgraph-realworld/blob/main/.agents/skills/crear_caso/SKILL.md) antes de ejecutar cualquier tarea.

---

## Estado actual

10 casos operativos e industriales: 01, 02, 03, 04, 05, 09, 10, 13, 19, 25.
15 casos scaffold listos para elevar.

---

## Orden de elevacion de casos

```
SCAFFOLD  →  (SKILL.md)  →  OPERATIVO  →  (observabilidad + hardening)  →  INDUSTRIAL
```

### Ola 1 — Alta prioridad

| Caso | Dominio | Por que |
|:---|:---|:---|
| ~~04 — SOC Triage~~ | Seguridad | **COMPLETADO v4.1.0** — Router de riesgo, threat intel, SIEM context |
| ~~05 — Analista de Documentos~~ | Legal / Contratos | **COMPLETADO v4.2.0** — 7 nodos, router de riesgo, 3 docs DEMO |
| 17 — Legal Intake | Legal | Continuacion natural del 05. Clasificacion + routing a especialistas. |

### Ola 2 — Impacto comercial

| Caso | Dominio |
|:---|:---|
| 08 — Ventas B2B + CRM | Comercial |
| 14 — Finanzas: Conciliacion | Finanzas |
| 06 — Compliance & Auditorias | Gobernanza |
| 21 — Documentacion Automatica | DevOps |

### Ola 3 — Dominio especializado

07, 11, 12, 15, 18, 22, 24, 16, 20, 23 — segun disponibilidad y demanda.

---

## Mejoras transversales pendientes (v4.1.0)

| Caso | Integracion pendiente |
|:---:|:---|
| 03 | PagerDuty + Datadog reales |
| 10 | HRIS, IAM, Slack, correo (4 TODO REAL) |
| 19 | GitHub API real (GITHUB_TOKEN) |
| 25 | APIs financieras/legales reales |

Casos 03, 19, 25 pendientes de elevacion a INDUSTRIAL: compose.smoke, logging JSON estructurado, /metrics documentado, OAuth2 verificado en tests.

---

## Largo plazo

- Kubernetes con NetworkPolicy y SecurityContext completos.
- IaC (Terraform / Pulumi) para entornos reproducibles en cloud.
- OpenTelemetry para trazas distribuidas entre servicios.
- Secret manager externo (Vault, AWS Secrets Manager).

---

Para el detalle completo con enlaces a todos los documentos, ver [ROADMAP.md en el repositorio](https://github.com/vladimiracunadev-create/langgraph-realworld/blob/main/ROADMAP.md).
