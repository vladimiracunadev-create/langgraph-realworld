# Changelog

Todos los cambios notables del repositorio se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## v4.6.0 — 2026-05-05

### Agregado

- **Caso 06 — Compliance & Auditorías elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 8 nodos: `parsear_alcance → mapear_controles → recopilar_evidencias → {router severidad: escalar_responsable | validar_evidencias} → generar_expediente → log_trazabilidad → producir_resumen`. Router condicional ramifica por severidad de faltantes; el camino "alta" pasa por `escalar_responsable` antes de validar.
  - Cadena de custodia SHA-256 encadenada (append-only): cada acción del agente queda registrada con `seq`, `ts` UTC ISO-8601, `accion`, `detalle` canonicalizado, `prev_hash` y `hash`. La primera entrada usa `prev_hash="GENESIS"`. Modificar cualquier `detalle` rompe la cadena en todas las entradas posteriores.
  - 3 marcos regulatorios soportados: ISO 27001:2022 (4 controles A.5.1, A.5.15, A.8.16, A.8.28), SOC 2 Type II (CC6.1, CC7.2, CC8.1, A1.2) y GDPR (Art.30 ROPA, Art.32, Art.33, Art.35 DPIA). Catálogo extensible en `data/marcos.json` con título, fuente (documentacion/iam/siem/git/monitoring/ticketing), owner por email y criticidad alta/media.
  - Score de cumplimiento 0-100: controles completos cuentan 100, parciales 50, sin evidencia 0. Indicador verde/amarillo/rojo según umbrales (verde ≥95 sin sin_evidencia, amarillo ≥75, rojo <75).
  - Validación de evidencias determinista: campos obligatorios, sistemas válidos, antigüedad máxima 365d, alerta a 180d, fechas dentro de período (acepta `YYYY-Qn`, `YYYY-MM` y `YYYY`).
  - Modo DEMO: 3 escenarios calibrados (`AUD-001` ISO limpio score 100 riesgo verde, `AUD-002` SOC 2 con faltantes en CC6.1/CC7.2 escala a IAM y SOC, `AUD-003` GDPR con ROPA Nov-2024 y DPIA Ago-2024 vencidas → evidencias inválidas y escalación al DPO). Funciona sin OPENAI_API_KEY.
  - Modo LIVE: GPT-4o-mini redacta resumen ejecutivo para comité de auditoría.
  - 26 tests (15 graph flow + 11 API) — todos verdes. Cubren: hash chain encadenamiento, periodo bounds, router severidad, end-to-end por escenario, consistencia de métricas y eventos.
  - Docker: Dockerfile non-root + compose.yml aislado (puerto 8006). Imagen Python 3.11-slim con curl para healthcheck.
  - UI dark theme acento índigo (#818cf8) con selector de auditoría, vista previa de marco/periodo/resultado esperado, badge DEMO/LIVE, timeline streaming NDJSON, KPIs (controles OK/parciales/sin/evidencias inválidas), tabla índice por control con estado coloreado (verde/amarillo/rojo), tarjetas por faltante y por evidencia inválida, panel de escalaciones con cuerpo de email, visor de cadena de custodia con seq/timestamp/acción/hash y resumen ejecutivo.
- **ROADMAP v4.6.0**: caso 06 movido de scaffold a operativos (14 casos totales). Pendientes Ola 2: caso 21 (Documentación Automática).

### Modificado

- `README.md`: badge de versión → 4.6.0, contador de operativos 13 → 14, caso 06 movido de scaffold a OPERATIVO en ambas tablas.
- `ROADMAP.md`: versión → 4.6.0, caso 06 marcado como completado, scaffolds 12 → 11.
- `index.html` portal: tarjeta de caso 06 actualizada de LEGACY → OPERATIVO con enlace al backend `http://localhost:8006/`.

---

## v4.5.0 — 2026-05-04

### Agregado

- **Caso 14 — Finanzas: Conciliación elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 9 nodos: `normalizar_transacciones → clasificar_transacciones → matching_automatico → detectar_outliers → proponer_ajuste → escalar_auditoria → marcar_partida_en_transito → generar_reporte_cuadre → producir_resumen`. Las 3 ramas de discrepancia se ejecutan en serie y filtran el array `outliers` por su `tipo`, evitando merge de estado por bifurcación.
  - Matching automático multi-criterio con score 1.0/0.7/0.6: exact match (referencia + fecha ±1 día + monto), match amplio (fecha ±3 días + monto), match por contraparte (sin referencia). Tolerancia de monto configurable (`tolerancia_monto_pesos: 1000`).
  - Detección de outliers determinista con z-score sobre histórico del propio escenario (umbral 2.5σ), implementado en Python puro (`math.sqrt`) sin pandas/numpy/scikit-learn — mantiene el caso ligero y consistente con los demás del repo.
  - Clasificación de discrepancias en 3 tipos: (a) `error_contable` con asiento contable sugerido (cuenta origen → cuenta destino, débito/haber, monto absoluto), (b) `posible_fraude` que escala a auditoría interna con nota formal incluyendo motivo, severidad y acción requerida, (c) `partida_en_transito` para diferencias legítimas de timing (cheques emitidos no cobrados, depósitos en cola al cierre).
  - Detección de fraude por señales combinadas: contraparte con keywords offshore (`llc`, `panamá`, `bvi`, `offshore`, `trust`), descripción atípica (`urgente`, `consultoría exterior`), monto mínimo configurable (20M CLP).
  - Indicador de riesgo verde/amarillo/rojo según porcentaje de cuadre, presencia de ajustes y escalaciones.
  - Modo DEMO: 3 escenarios calibrados (`SCN-001` cierre limpio 100% riesgo verde, `SCN-002` 91% con ajustes y partidas en tránsito riesgo amarillo, `SCN-003` 20% con transferencia offshore de 47.8M CLP a "Servicios Globales LLC (Panamá)" riesgo rojo). Funciona sin OPENAI_API_KEY.
  - Modo LIVE: GPT-4o-mini redacta justificación contable formal de cada ajuste y resumen ejecutivo para el controller.
  - Categorías contables predefinidas en `account_mapping.json` (remuneraciones, arriendo, servicios básicos, suministros, equipos, ventas, impuestos, comisiones bancarias, servicios profesionales, transferencias internacionales, otros) con cuenta + centro de costo + keywords de matching.
  - 22 tests (13 graph flow + 9 API) — todos verdes.
  - Docker: Dockerfile non-root + compose.yml aislado (puerto 8014).
  - UI dark theme con selector de período, vista previa del escenario, badge DEMO/LIVE, timeline streaming NDJSON, KPIs en grilla (totales banco/contable/conciliado/pendiente), tabla de matches con score y criterio, tarjetas por outlier coloreadas según tipo (rojo fraude, amarillo error, verde tránsito), asientos contables sugeridos, notas de escalación a auditoría, reporte de cuadre tipográfico monoespaciado y resumen ejecutivo.
- **ROADMAP v4.5.0**: caso 14 movido de Ola 2 a operativos (13 casos totales). Pendientes Ola 2: casos 06 (Compliance) y 21 (Documentación Automática).

### Modificado

- `README.md`: badge de versión → 4.5.0, contador de operativos 12 → 13, caso 14 movido de scaffold a OPERATIVO en ambas tablas.
- `ROADMAP.md`: versión → 4.5.0, caso 14 marcado como completado, scaffolds 13 → 12.
- `docker-compose.yml` raíz: servicio `case14` cambiado de demo nginx (puerto 9014) a backend real FastAPI (puerto 8014) con volúmenes `data/` y `web/`.
- `index.html` portal: tarjeta de caso 14 actualizada de LEGACY → OPERATIVO con enlace al backend `http://localhost:8014/`.

---

## v4.4.0 — 2026-05-04

### Agregado

- **Caso 08 — Ventas B2B + CRM elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 10 nodos y 2 routers condicionales: `investigar_cuenta → calificar_lead → [router score_icp → descartar | personalizar_outreach → seleccionar_canal → simular_envio → monitorear_respuesta → router señal_interes → {escalar_ejecutivo | programar_followup | descartar}] → actualizar_crm → producir_resumen`.
  - Scoring ICP determinista (0-100) ponderando industria prioritaria, tamaño de empresa, modernidad del stack tecnológico, señales de compra activas y noticias recientes; configurable vía `icp.json`.
  - Selección automática de canal y cadencia: C-level → email + LinkedIn (3 toques en días 0/4/8); roles intermedios → email solo (2 toques en días 0/5).
  - Plantillas de outreach por industria (logistics, fintech, media, default) con sustitución de variables `{{company_name}}`, `{{contacto_nombre}}`, `{{benchmark}}`, `{{tech_observado}}`.
  - Asignación de AE por industria + país + menor `deals_activos`, con 4 ejecutivos comerciales en `sales_reps.json`.
  - Estados de CRM finales: `Meeting Scheduled`, `Nurturing`, `Closed Lost`, `Disqualified`. Notas y `next_step` consolidados en cada record.
  - Modo DEMO: 4 cuentas (`ACC-001` Logistics mid-market positiva, `ACC-002` Gaming startup sin respuesta, `ACC-003` Retail tradicional fuera_icp, `ACC-004` Banca enterprise con freeze de vendors negativo) que ejercitan los 4 caminos del pipeline.
  - Modo LIVE: GPT-4o-mini mejora la redacción del mensaje de outreach y genera el resumen ejecutivo si hay credenciales.
  - 23 tests (14 graph flow + 9 API) — todos verdes.
  - Docker: Dockerfile non-root + compose.yml aislado (puerto 8008).
  - UI dark theme con selector de cuenta, vista previa de empresa/tech/noticias, badge DEMO/LIVE, timeline streaming NDJSON, panel de razones del scoring ICP, mock-up de email del outreach, cadencia visual, señal del prospect con color, ficha del AE asignado, registro CRM y resumen ejecutivo.
- **ROADMAP v4.4.0**: caso 08 movido de Ola 2 a operativos (12 casos totales). Siguiente Ola 2: casos 14, 06, 21.

### Modificado

- `README.md`: badge de versión → 4.4.0, contador de operativos 11 → 12, caso 08 movido de scaffold a OPERATIVO en ambas tablas.
- `ROADMAP.md`: versión → 4.4.0, caso 08 marcado como completado, scaffolds 14 → 13.
- `docker-compose.yml` raíz: servicio `case08` cambiado de demo nginx (puerto 9008) a backend real FastAPI (puerto 8008) con volúmenes `data/` y `web/`.
- `index.html` portal: tarjeta de caso 08 actualizada de LEGACY → OPERATIVO con enlace al backend `http://localhost:8008/`.

---

## v4.3.0 — 2026-05-04

### Agregado

- **Caso 17 — Legal Intake elevado a OPERATIVO**: backend FastAPI + LangGraph completo con modo DEMO/LIVE.
  - `StateGraph` con 10 nodos y 2 routers condicionales: `recibir_solicitud → entrevista_inicial → clasificar_tipo_caso → [router especialidad → recopilar_hechos_{laboral|mercantil|civil}] → validar_informacion → [router completitud → solicitar_informacion_faltante] → evaluar_urgencia → generar_borrador_documento → asignar_abogado → producir_resumen_intake`.
  - Clasificación por especialidad legal mediante keyword scoring sobre `specialty_keywords.json` (laboral, mercantil, civil) y detección de subtipo (despido injustificado, incumplimiento contractual, sucesión intestada, etc.).
  - Extracción heurística DEMO de hechos estructurados desde el relato libre del cliente (montos, fechas, causales legales, partes, evidencia documental).
  - Validación de completitud contra campos requeridos por subtipo (`required_fields.json`); branch separado para registrar preguntas pendientes al cliente sin bloquear la generación del borrador.
  - Evaluación de urgencia procesal usando matriz de plazos legales típicos (60 días art. 168 CT, prescripción de títulos ejecutivos, etc.).
  - Generación de borrador inicial con plantillas (`templates.json`): demanda laboral, requerimiento extrajudicial, posesión efectiva. Placeholders no resueltos quedan marcados como `{{PENDIENTE: campo}}` para el abogado revisor.
  - Asignación automática del abogado responsable por especialidad y carga (`lawyers.json`, 6 abogados con casos activos simulados).
  - Modo DEMO: 3 intakes realistas (`INT-001` despido, `INT-002` incumplimiento contractual con cláusula penal, `INT-003` sucesión intestada con info faltante). Funciona sin OPENAI_API_KEY.
  - Modo LIVE: GPT-4o-mini mejora la redacción del borrador y el resumen ejecutivo si hay credenciales.
  - 26 tests (16 graph flow + 10 API) — todos verdes.
  - Docker: Dockerfile non-root + compose.yml aislado con volumen data/ read-only (puerto 8017).
  - UI dark theme con selector de intake, vista previa de la solicitud, badge DEMO/LIVE, timeline streaming NDJSON, panel de hechos extraídos, preguntas pendientes, borrador con highlight de placeholders, ficha del abogado asignado y resumen ejecutivo.
- **ROADMAP v4.3.0**: caso 17 movido de Ola 1 a operativos (11 casos totales). Siguiente Ola 2: casos 08, 14, 06, 21.

### Modificado

- `README.md`: badge de versión → 4.3.0, contador de operativos 10 → 11, caso 17 movido de scaffold a OPERATIVO en ambas tablas.
- `ROADMAP.md`: versión → 4.3.0, caso 17 marcado como completado, scaffolds 15 → 14.
- `docker-compose.yml` raíz: servicio `case17` cambiado de demo nginx (puerto 9017) a backend real FastAPI (puerto 8017) con volumen `data/` y `web/`.
- `index.html` portal: tarjeta de caso 17 actualizada de LEGACY → OPERATIVO con enlace al backend `http://localhost:8017/`.

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
