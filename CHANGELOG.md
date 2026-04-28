# Changelog

Todos los cambios notables del repositorio se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## v4.2.0 — 2026-04-28

### Agregado

- **Caso 05 — Analista de Documentos elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 7 nodos y 1 router condicional: `ingesta_texto → segmentar_secciones → extraer_clausulas → clasificar_riesgos → [escalar_revision_legal →] generar_checklist → producir_resumen_ejecutivo`.
  - Keyword extraction sobre secciones contractuales segmentadas por regex (CLÁUSULA, ARTÍCULO, SECCIÓN, CONSIDERANDOS, etc.).
  - Score de riesgo compuesto (0-100) a partir de cláusulas detectadas; router dirige a escalación legal solo si riesgo es ALTO.
  - Modo DEMO: lógica determinista sobre 3 documentos locales (NDA/bajo, Servicios TI/medio, Licitación/alto) y 8 patrones de cláusulas en `clause_patterns.json`.
  - Modo LIVE: GPT-4o-mini ajusta el score de riesgo y genera resumen ejecutivo narrativo.
  - 27 tests (18 graph flow + 9 API) — todos pasando.
  - Docker: Dockerfile non-root + compose.yml con volumen data/ read-only (puerto 8005).
  - UI dark theme con selector de documento, badge DEMO/LIVE, timeline de nodos y panel de resultados (cláusulas, checklist, resumen ejecutivo, escalación).
- **ROADMAP v4.2.0**: caso 05 movido de scaffold a operativos (10 casos totales). Siguiente Ola 1: caso 17 (Legal Intake).

### Modificado

- `README.md`: badge de versión → 4.2.0, contador de casos operativos 9 → 10, taxonomía corregida (caso 05 en OPERATIVO).
- `ROADMAP.md`: versión → 4.2.0, caso 05 marcado como completado, scaffolds 16 → 15.
- `docs/ARCHITECTURE.md`, `docs/wiki/Home.md`, `docs/wiki/Roadmap.md`, `docs/wiki/README.md`, `docs/wiki/_Sidebar.md`: versión → 4.2.0, 10 operativos.

---

## v4.1.0 — 2026-04-22

### Agregado

- **Caso 04 — SOC Triage de Alertas elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 8 nodos y 2 routers condicionales: `normalizar_alerta → enriquecer_ioc → correlacionar_eventos → evaluar_riesgo → [cerrar_automatico | investigacion_adicional → decision | escalar_analista → generar_informe_triage]`.
  - Score de riesgo compuesto (0-100) que pondera reputación de IOCs (VirusTotal/AbuseIPDB), desviación del baseline SIEM y severidad de la fuente.
  - Modo DEMO: lógica determinista sobre `alerts.json` (5 alertas reales: brute force SSH, nmap, Emotet, DNS C2, off-hours login) y `threat_intel.json` (IP reputation + file hashes + dominios + MITRE ATT&CK mapping).
  - Modo LIVE: GPT-4o-mini ajusta el score de riesgo y redacta el informe de triage narrativo.
  - Stubs de VirusTotal, AbuseIPDB, MISP, Splunk/Elastic y JIRA/ServiceNow listos para reemplazar por APIs reales.
  - 19 tests (7 API + 12 graph flow) — todos pasando.
  - Docker: Dockerfile + compose.yml + `.env.example` (puerto 8004).
- **`.secrets.baseline` actualizado**: hashes MD5 de malware demo registrados como falsos positivos conocidos.
- **ROADMAP v4.1.0**: caso 04 movido de scaffold a operativos (9 casos totales). Siguiente Ola 1: caso 05 (Analista de Documentos).

### Modificado

- `README.md`: badge de versión → 4.1.0, contador de casos operativos 8 → 9, tabla de estados actualizada, taxonomía corregida.
- `index.html`: caso 04 badge `LEGACY` → `OPERATIVO`, enlace al backend (puerto 8004).
- `docs/ARCHITECTURE.md`, `docs/wiki/Home.md`, `docs/wiki/Roadmap.md`, `docs/wiki/_Sidebar.md`: versión → 4.1.0, 9 operativos.

### Seguridad / Despliegue

- **`security.yml` — detect-secrets**: agregado `--exclude-files 'cases/.*/data/'` al paso de full filesystem scan para excluir hashes MD5 de IOCs de malware demo (falsos positivos). Consistente con la exclusión ya existente en el job `supply_chain`.
- **`security.yml` — grype matrix**: caso 04 añadido al escaneo de imagen Docker.
- **CVEs resueltos en los 9 backends** — lockfiles regenerados con `pip-compile`:

  | Paquete | Antes | Después | Referencia |
  |---|---|---|---|
  | `langsmith` | 0.7.30 | 0.7.31 | GHSA-rr7j-v2q5-chgv |
  | `langchain-openai` | 1.1.12 | 1.1.14 | GHSA-r7w7-9xr2-qq2r |
  | `langchain-core` | 1.2.28 | 1.3.0 | transitivo (requerido por langchain-openai 1.1.14) |
  | `lxml` *(caso 09)* | 6.0.3 | 6.1.0 | CVE-2026-41066 |
  | `pypdf` *(caso 09)* | 6.10.0 | 6.10.2 | GHSA-jj6c / GHSA-4pxv / GHSA-7gw9 / GHSA-x284 |

- **`requirements.in` de los 9 casos**: pins mínimos actualizados para que futuros `pip-compile` no regresen a versiones vulnerables.

---

## v4.0.1 — 2026-04-10

### Agregado

- **Interfaces web `backend/web/index.html`** para los casos 03, 19 y 25 (faltaban completamente).
  Cada interfaz incluye: hero en español con descripción del flujo, badge DEMO/LIVE, enlace `← VOLVER AL HUB` a `http://localhost:8080/`, pillrow de tecnologías, timeline de eventos en vivo via NDJSON streaming y panel de resultados con badges y listas.
  - **Caso 03 — Incident Response**: select INC-001/INC-002/INC-003, timeline de severidad P1/P2/P3, recovery checks, postmortem.
  - **Caso 19 — DevEx PR Review**: select PR-001/PR-042/PR-105, timeline de hallazgos por severidad, decision badge (REQUEST_CHANGES/APPROVE_WITH_COMMENTS/APPROVE).
  - **Caso 25 — Supervisor/Workers**: select DDL-2026-001/002/003, workers timeline con iconos, viability score coloreado, conflictos detectados y condiciones para proceder.
- **Datos DEMO completos** para casos 19 y 25:
  - `cases/19-devex-pr-review/data/sample_pr.json`: convertido de objeto único a array con 3 PRs distintos. PR-001 (SQL injection + eval → CRITICAL), PR-042 (creds hardcodeadas + shell injection → HIGH), PR-105 (solo docs → APPROVE).
  - `cases/25-supervisor-workers/data/sample_task.json`: convertido de objeto único a array con 3 tareas distintas. DDL-2026-001 (TechStartup $5M), DDL-2026-002 (FinTech $3.2M), DDL-2026-003 (CloudData $12M).
- **Sección "Estandar de la interfaz web"** en `.agents/skills/crear_caso/SKILL.md`: define qué es y qué NO es un caso (no es un link a JSON, no es una página sin UI, DEMO siempre funciona, datos deben cubrir todas las opciones del select).

### Corregido

- `cases/19-devex-pr-review/backend/src/integrations.py`: fallback gracioso a stub en vez de `ValueError` cuando el `pr_id` solicitado no existe en el JSON de datos.
- `index.html` (hub raíz): casos 03, 19 y 25 marcados como `OPERATIVO` con links correctos a `http://localhost:8003/web/`, `http://localhost:8019/web/` y `http://localhost:8025/web/`.

---

## v4.0.0 — 2026-04-09

### Agregado

- **Casos 03, 19, 25 elevados a OPERATIVO**: backends FastAPI + LangGraph completos con modo DEMO/LIVE, tests, Docker y CI.
  - **Caso 03** — Incident Response SRE: StateGraph con HITL auto-aprobado en DEMO, runbooks P1/P2/P3, integrations stub (PagerDuty, remediación, recovery), postmortem.
  - **Caso 19** — DevEx PR Review: análisis de seguridad/calidad/tests sobre diffs con detección de patrones (SQL injection, eval, imports), router por nivel de riesgo, changelog automático.
  - **Caso 25** — Supervisor/Workers: patrón multi-agente con 4 workers (financial, legal, operational, reputational), acumulación de resultados con `Annotated[list, operator.add]`, reconciliación y detección de conflictos.
- **OAuth2/OIDC opt-in** en todos los backends: nuevo módulo `auth.py` por caso con validación JWT vía JWKS. `USE_OAUTH2=false` por defecto (backward-compatible). Activa con `USE_OAUTH2=true` + `OAUTH2_JWKS_URL`.
- **Logging JSON estructurado** estandarizado en los 8 backends operativos: `ContextVar` + `TraceIdFilter` + `LOG_FORMAT` JSON + `X-Trace-ID` en respuestas. Los casos 01, 02 y 13 ahora tienen el mismo nivel de observabilidad que 09 y 10.
- **Endpoint `/metrics`** en todos los backends: uptime, requests_total, errors_total, avg_latency_ms, modo DEMO/LIVE, langsmith_enabled, oauth2_enabled.
- **LangSmith opt-in**: `langsmith` agregado a `requirements.in/txt` de los 8 casos. Activar con `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY`. Sin credenciales, LangSmith permanece inactivo (modo DEMO intacto).
- **Nginx reverse proxy + TLS**: `nginx/` con Dockerfile, `nginx.conf`, `conf.d/default.conf` (8 upstreams), `scripts/gen-certs.sh` (self-signed para dev). `docker-compose.tls.yml` como override sin tocar el compose principal.
- **pip-compile workflow**: `requirements.in` para los 8 casos operativos, `scripts/pip-compile-all.sh` con modo `--check`, job `dependency_lock_check` en CI.
- **Seguridad CI mejorada**: grype con `fail-build: true` + `.grype.yaml` (`only-fixed: true`). detect-secrets con escaneo completo del filesystem y últimos 50 commits del git history.

### Modificado

- `docker-compose.yml`: agregados case03, case19, case25 (ports en `127.0.0.1`).
- `docker-compose.tls.yml`: 3 casos nuevos con ports reseteados para acceso solo vía nginx.
- `nginx/conf.d/default.conf`: upstreams y locations para case03, case19, case25.
- `.github/workflows/ci.yml`: jobs `python_case03`, `python_case19`, `python_case25` + `dependency_lock_check`.
- `.github/workflows/security.yml`: 3 casos nuevos en matrix de grype, `fail-build: true`, steps de full-scan y git-history-scan en detect-secrets.
- `Makefile`: targets `test-case03`, `test-case19`, `test-case25`, `pip-compile`, `pip-compile-check`.
- `scripts/pip-compile-all.sh`: casos 03, 19, 25 incluidos en la lista de compilación.
- `cases/09, 10 api.py`: middleware refactorizado para usar `auth.py` centralizado; eliminado código duplicado.

---

## v3.9.0 — 2026-04-06

### Seguridad

- **Auditoría completa por 8 capas**: contenedor/proceso, red, credenciales, servidor web, herramientas, autenticación, CI/CD y cadena de suministro.
- **Capa 1 — Contenedor**: backends 01 y 02 con usuario `appuser` (non-root) y imagen pineada a `python:3.11.10-slim`. Backend 13 también pineado.
- **Capa 1 — Demos nginx**: todos los 25 casos con `nginx:1.27.3-alpine` (antes `nginx:alpine` flotante) y `USER nginx` con chown correcto.
- **Capa 1 — Healthcheck**: demos corregidas de `curl` (ausente en Alpine) a `wget --spider` (BusyBox nativo). Puertos de healthcheck de casos 02–25 corregidos de 8080 a 80.
- **Capa 2 — Red**: todos los puertos de `docker-compose.yml` vinculados a `127.0.0.1` para prevenir acceso desde la red local.
- **Capa 4 — Servidor web**: 25 `nginx.conf` actualizados con `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Content-Security-Policy` y `Permissions-Policy`.
- **Capa 7 — CI/CD**: Dependabot configurado para pip (raíz + 5 backends), GitHub Actions y Docker.
- **Capa 7 — CI/CD**: escaneo de imágenes Docker con `grype` (Anchore) pineado por SHA. Se eligió grype sobre Trivy por incidente de supply chain conocido.
- **Capa 8 — Supply chain**: job `supply_chain` en CI detecta caracteres Unicode bidi (CVE-2021-42574 "Trojan Source") y patrones de ofuscación (`exec+base64`, `eval()` dinámico, `os.system` con concatenación).

### Documentación

- `SECURITY.md` actualizado a v3.9.0 con tabla de estado por capa, riesgos aceptados y pendientes.
- `README.md` y `CHANGELOG.md` actualizados a v3.9.0.
- Todos los documentos revisados para consistencia de versión y ortografía.
- 20 READMEs de casos scaffold reescritos con flujos Mermaid, tablas de stack técnico y descripción de valor de negocio.

---

## v3.8.0 — 2026-04-06

### Agregado

- Fase 2 de hardening aplicada a los casos operativos con `DEMO_AUTH_TOKEN`, `RATE_LIMIT_RPM` y `TRUST_PROXY_HEADERS` como guardrails opcionales de exposición externa.
- Suite propia para el caso 02 (`pytest`) con validación de API, auth opcional, rate limiting y flujo LangGraph.
- Job dedicado en CI para el caso 02.

### Cambiado

- README, docs, wiki local, casos clave y Hub CLI sincronizados a v3.8.0.
- Documentación reescrita en ASCII para reducir drift y problemas de codificación.
- `hub.py` y la documentación del Hub alineados con la taxonomía `Operational/Industrial (v3.8.0)`.

### Seguridad — v3.8.0 — 2026-04-06

- Postura de seguridad actualizada para reflejar claramente controles implementados y límites de alcance.
- Guardrails de exposición externa documentados sin romper quickstart ni demos locales.
- CI y seguridad automatizada ahora reflejan el caso 02 como backend validado, no solo docker-build.

---

## v3.7.0 — 2026-04-02

### Agregado — v3.7.0 — 2026-04-02

- Caso 02 elevado a operacional con UI SRE, runbooks y nodos LangGraph adicionales.
- Frontend interactivo para el caso 02 con sugerencias y tracker de eventos.
- Rediseño del portal raíz hacia catálogo de automatizaciones IA.

---

## v3.6.0 — 2026-03-13

### Agregado — v3.6.0 — 2026-03-13

- Centro de APIs compartido para el portal y los casos operativos 01, 09, 10 y 13.
- Formulario de credenciales opcionales con nombre de variable, caso vinculado, enlace oficial y exportación `.env` por caso.
- Guía documental explícita para instalar primero y completar APIs después sin bloquear el modo DEMO.
