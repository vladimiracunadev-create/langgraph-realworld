# Costos de operación — DEMO vs LIVE

> **Versión**: 4.15.0 | **Filosofía**: DEMO-first. Todos los casos funcionan sin claves externas. LIVE es **opt-in caso por caso**.

Este documento responde a una pregunta concreta: *"el repo está operativo por DEMOs — ¿qué hace falta y cuánto cuesta para llevarlo a producción real?"*. La respuesta corta: la mayoría de casos cruza a LIVE con solo `OPENAI_API_KEY`. Hay tres casos con stubs de proveedores SaaS que requieren contratos enterprise.

---

## 1. Resumen ejecutivo

| Tier | Casos | Coste mensual aproximado | Qué desbloquea |
|---|---|---|---|
| 🟢 **DEMO puro** (sin coste) | 03, 04, 05, 06, 09, 21, 25 | **0 USD** | Flujo completo sin red — datos sintéticos |
| 🟡 **Solo OpenAI** (gpt-4o-mini) | 01, 02, 07, 08, 13, 14, 17, 19, 21 | **~5–20 USD** a 1M tokens/mes | LLM real para narrativa, justificaciones, resúmenes |
| 🔴 **Multi-integración enterprise** | 10 | **150–800 USD** + planes SaaS | HRIS, IAM, Slack, Google Workspace, GitHub, SMTP |
| 🔵 **Stubs de terceros pendientes** | 03, 04, 19, 25 | Variable | PagerDuty, VirusTotal, GitHub API, etc. |

> [!IMPORTANT]
> Los costes son estimaciones públicas basadas en pricing oficial al 2026-05-07. Verifica el pricing actual de cada proveedor antes de comprometer presupuesto.

---

## 2. Tabla maestra por caso

| ID | Caso | Modo LIVE requiere | Variables `.env` | Pricing público | Lo que desbloquea |
|---:|:---|:---|:---|:---|:---|
| 01 | [Soporte Omnicanal](../cases/01-soporte-cliente-omnicanal/README.md) | OpenAI | `OPENAI_API_KEY`, `OPENAI_MODEL` | ~$0.15/1M tok input | Clasificación + draft de respuestas |
| 02 | [Mesa Ayuda TI](../cases/02-mesa-ayuda-ti-runbooks/README.md) | OpenAI (opcional) | `OPENAI_API_KEY` | ~$0.15/1M tok | Enriquecimiento — runbooks deterministas en DEMO |
| 03 | [Incident Response SRE](../cases/03-incident-response-sre/README.md) | OpenAI + PagerDuty + Datadog (stubs) | `OPENAI_API_KEY`, `PAGERDUTY_TOKEN`, `DATADOG_API_KEY` | OpenAI + PagerDuty desde $25/u/mes + Datadog desde $15/host/mes | Paging real + métricas reales |
| 04 | [SOC Triage](../cases/04-soc-triage-alertas/README.md) | OpenAI + VirusTotal + AbuseIPDB + SIEM (stubs) | `OPENAI_API_KEY`, `VIRUSTOTAL_API_KEY`, `ABUSEIPDB_KEY`, `SPLUNK_TOKEN` | VT free/Premium $480/año, AbuseIPDB free, Splunk enterprise | Threat intel real + búsqueda SIEM |
| 05 | [Analista Documentos](../cases/05-analista-documentos/README.md) | OpenAI (opcional) | `OPENAI_API_KEY` | ~$0.15/1M tok | Narrativa contractual — extracción opt-in con `pymupdf`/`python-docx` |
| 06 | [Compliance & Auditorías](../cases/06-compliance-auditorias/README.md) | OpenAI (opcional) | `OPENAI_API_KEY` | ~$0.15/1M tok | Resumen ejecutivo para comité — cadena custodia SHA-256 ya determinista |
| 07 | [Compras y Abastecimiento](../cases/07-compras-abastecimiento/README.md) | OpenAI (opcional) | `OPENAI_API_KEY` | ~$0.15/1M tok | Justificación de recomendación + nota de escalación |
| 08 | [Ventas B2B + CRM](../cases/08-ventas-b2b-crm/README.md) | OpenAI; CRM (HubSpot/Salesforce) stub | `OPENAI_API_KEY`, `HUBSPOT_API_KEY` | OpenAI + HubSpot Sales desde $90/u/mes | Outreach personalizado + sync CRM |
| 09 | [RRHH Screening](../cases/09-rrhh-screening-agenda/README.md) | DEMO completo; OpenAI opcional | `OPENAI_API_KEY` | ~$0.15/1M tok | Resumen de candidato — calendario es determinista |
| 10 | [Onboarding Empleados](../cases/10-onboarding-empleados/README.md) | **6 integraciones reales** | `OPENAI_API_KEY`, `GOOGLE_ADMIN_CREDENTIALS_JSON`, `SLACK_BOT_TOKEN`, `GITHUB_TOKEN`, `AWS_ACCESS_KEY_ID`, `SMTP_SERVER` | Google Workspace $14.40/u/mes + Slack $7.25/u/mes + GitHub $4/u/mes + AWS pay-as-you-go | Provisioning real (cuenta, canales, repos, IAM) |
| 13 | [Analista BI](../cases/13-bi-analista-datos/README.md) | OpenAI | `OPENAI_API_KEY` | ~$0.15/1M tok | SQL agent + narrativa de chart |
| 14 | [Finanzas Conciliación](../cases/14-finanzas-conciliacion/README.md) | OpenAI; ERP (SAP/Oracle/Quickbooks) stub | `OPENAI_API_KEY` | ~$0.15/1M tok + licencias ERP existentes | Justificación contable + resumen para CFO |
| 17 | [Legal Intake](../cases/17-legal-intake/README.md) | OpenAI | `OPENAI_API_KEY` | ~$0.15/1M tok | Clasificación + plantillas con LLM |
| 19 | [DevEx PR Review](../cases/19-devex-pr-review/README.md) | OpenAI + GitHub API (stub) | `OPENAI_API_KEY`, `GITHUB_TOKEN` | OpenAI + GitHub free/Team $4/u/mes | Reviews automáticos sobre PRs reales |
| 21 | [Documentación Auto](../cases/21-docs-auto/README.md) | OpenAI (opcional) | `OPENAI_API_KEY` | ~$0.15/1M tok | Resumen ejecutivo — redacción ya determinista |
| 25 | [Supervisor + Workers](../cases/25-supervisor-workers/README.md) | DEMO completo; APIs financieras/legales por definir | `OPENAI_API_KEY` | ~$0.15/1M tok | Workers reales (due diligence, etc.) |

> [!NOTE]
> Las columnas "stubs" indican que el código tiene la estructura preparada pero **no implementa el cliente HTTP real** todavía. Son trabajo pendiente declarado en [ROADMAP.md](../ROADMAP.md).

---

## 3. Infraestructura transversal

| Componente | Proveedor | Variables | Pricing | Obligatorio |
|:---|:---|:---|:---|:---:|
| **LLM backbone** | OpenAI (`gpt-4o-mini` por defecto) | `OPENAI_API_KEY`, `OPENAI_MODEL` | $0.15 input + $0.60 output / 1M tokens | No (DEMO sin él) |
| **Observabilidad** | LangSmith | `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` | Free 5K trazas/mes · Plus $39/u/mes | No |
| **Hosting local** | Docker Desktop / docker compose | — | Gratis (uso personal/SMB <10 empleados) | Sí (modo Docker) |
| **Hosting cloud** | Fly.io · Railway · AWS ECS | — | ~$10–50/mes 1 caso · ~$150–650/mes portfolio completo (ver [CLOUD_AWS.md](CLOUD_AWS.md)) | No |
| **Secretos** | `.env` local · AWS Secrets Manager · HashiCorp Vault | depende del backend elegido | $0.40/secreto/mes (AWS) | No |
| **Checkpoints LangGraph** | `MemorySaver` in-process / SQLite local | — | Gratis | Ya integrado |
| **Auth (opt-in)** | OAuth2/OIDC (Auth0, Cognito, Keycloak) | `USE_OAUTH2=true`, `OAUTH2_JWKS_URL`, `OAUTH2_AUDIENCE`, `OAUTH2_ISSUER` | Auth0 free 25K usuarios · Cognito $0.0055/MAU | No |

---

## 4. Receta para activar LIVE en un caso

```bash
# 1. Copiar plantilla de variables
cp cases/XX-slug/backend/.env.example cases/XX-slug/backend/.env

# 2. Completar credenciales (al menos OPENAI_API_KEY)
$EDITOR cases/XX-slug/backend/.env
# OPENAI_API_KEY=sk-proj-...
# OPENAI_MODEL=gpt-4o-mini

# 3. Levantar el caso (Docker o local)
docker compose up caseXX
# o:
cd cases/XX-slug/backend && uvicorn src.api:app --port 80XX

# 4. Verificar el modo
curl http://localhost:80XX/health
# {"status":"ok","mode":"LIVE",...}
```

El badge en la UI cambia automáticamente de 🟡 DEMO a 🟢 LIVE. El flujo del grafo no cambia — solo los nodos LLM-opcionales activan el cliente real con fallback al texto determinista si OpenAI está caído.

---

## 5. Estimación de coste por escenario de uso

### 🧪 Lab personal / portfolio
**~5 USD/mes** — solo `OPENAI_API_KEY`, ejecuciones esporádicas (<1M tokens), Docker local. Suficiente para todos los casos OpenAI-only y los DEMO puros.

### 🏢 Demo comercial / piloto interno
**~50 USD/mes** — OpenAI con tráfico moderado, LangSmith Plus para trazas, hosting Fly.io 1 caso operativo. Sin integraciones SaaS reales.

### 🏭 Despliegue productivo (1 caso enterprise, p. ej. caso 10)
**~600–1,200 USD/mes** — OpenAI + Google Workspace + Slack Business+ + GitHub Team + AWS IAM + SMTP transactional + secret manager + observabilidad + cloud hosting con HA. Variabiliza con número de empleados.

### ☁️ Migración AWS completa
Ver guía dedicada en [CLOUD_AWS.md](CLOUD_AWS.md): PoC ~25 USD · Producción ~180 USD · Enterprise ~650 USD.

---

## 6. Lo que **no** cuesta

- Todos los stubs DEMO funcionan sin internet — útil para demos en cliente, talleres y CI.
- El portfolio completo en local consume **~600 MB RAM** con todos los servicios levantados (medido v4.14.0).
- No hay vendor lock-in: el cliente OpenAI se puede sustituir por un provider local (Ollama, vLLM, Anthropic, Mistral) cambiando 4 líneas en `_llm_invoke()` de cada caso.
- No hay licencias propietarias: stack es Apache 2.0 / MIT (FastAPI, LangGraph, Pydantic).

---

## 7. Referencias

- [docs/INSTALL.md](INSTALL.md) — cómo levantar local / Docker / Hub CLI
- [docs/CLOUD_AWS.md](CLOUD_AWS.md) — migración a AWS con costes detallados
- [docs/REQUIREMENTS.md](REQUIREMENTS.md) — requisitos sistema y APIs opcionales
- [ROADMAP.md](../ROADMAP.md) — integraciones reales pendientes por caso
- `cases/*/backend/.env.example` — plantillas por caso
