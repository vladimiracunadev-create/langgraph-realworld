# Changelog

## v4.5.0 - 2026-05-04

### Added

- Caso 14 — Finanzas: Conciliacion elevado a OPERATIVO: 9 nodos LangGraph, matching multi-criterio (score 1.0/0.7/0.6), deteccion de outliers por z-score (umbral 2.5σ) en Python puro sin pandas/numpy, 3 tipos de discrepancia (error contable, posible fraude, partida en transito), 3 escenarios DEMO (cierre limpio verde, ajustes amarillo, fraude offshore rojo), streaming NDJSON, UI con KPIs + tabla de matches + tarjetas por outlier en puerto 8014.
- Suite de tests del caso 14: 22 tests (13 de grafo + 9 de API) todos en verde.

### Changed

- Total de backends operativos: 13 (01, 02, 03, 04, 05, 08, 09, 10, 13, 14, 17, 19, 25).
- Total de scaffolds: 12.
- Version bumped a 4.5.0 en README, docs, wiki, pyproject.toml y case.yml del caso 14.

---

## v4.4.0 - 2026-05-04

### Added

- Caso 08 — Ventas B2B + CRM elevado a OPERATIVO: 10 nodos LangGraph, 2 routers condicionales (score_icp + senal_interes), scoring ICP determinista 0-100 con pesos por industria/tamano/stack/senales, plantillas de outreach por industria (logistics/fintech/media/default), seleccion automatica de canal y cadencia segun nivel del contacto (C-level vs. otros), asignacion de AE por industria + carga, 4 deal_stages (Meeting Scheduled, Nurturing, Closed Lost, Disqualified), 4 cuentas DEMO en puerto 8008.
- Suite de tests del caso 08: 23 tests (14 de grafo + 9 de API) todos en verde.

### Changed

- Total de backends operativos: 12.
- Total de scaffolds: 13.

---

## v4.3.0 - 2026-05-04

### Added

- Caso 17 — Legal Intake elevado a OPERATIVO: 10 nodos LangGraph, 2 routers (especialidad + completitud), 3 especialidades legales (laboral, mercantil, civil) con extraccion heuristica de hechos, validacion de campos requeridos por subtipo, evaluacion de urgencia procesal por matriz de plazos legales, 3 plantillas de documentos (demanda laboral, requerimiento extrajudicial, posesion efectiva) con placeholders `{{PENDIENTE}}` para gaps, asignacion automatica de abogado por especialidad + carga, 3 intakes DEMO en puerto 8017.
- Suite de tests del caso 17: 26 tests (16 de grafo + 10 de API) todos en verde.

### Changed

- Total de backends operativos: 11.
- Total de scaffolds: 14.

---

## v4.2.0 - 2026-04-28

### Added

- Caso 05 — Analista de Documentos elevado a OPERATIVO: 7 nodos LangGraph, router condicional de riesgo, 3 documentos DEMO (NDA, SLA, licitacion), streaming NDJSON, UI interactiva en puerto 8005.
- Suite de tests completa para caso 05: 27 tests (18 de grafo + 9 de API) todos en verde.

### Changed

- Total de backends operativos: 10 (01, 02, 03, 04, 05, 09, 10, 13, 19, 25).
- Total de scaffolds: 15.
- Version bumped a 4.2.0 en README, docs, wiki y case.yml del caso 05.

---

## v3.9.0 - 2026-04-06

### Added

- Fase 2 de hardening aplicada a los casos operativos con `DEMO_AUTH_TOKEN`, `RATE_LIMIT_RPM` y `TRUST_PROXY_HEADERS` como guardrails opcionales de exposicion externa.
- Suite propia para el caso 02 (`pytest`) con validacion de API, auth opcional, rate limiting y flujo LangGraph.
- Job dedicado en CI para el caso 02.

### Changed

- README, docs, wiki local, casos clave y Hub CLI sincronizados a `v3.9.0`.
- Documentacion reescrita en ASCII para reducir drift y problemas de codificacion.
- `hub.py` y la documentacion del Hub alineados con la taxonomia `Operational/Industrial (v3.9.0)`.

### Security

- Postura de seguridad actualizada para reflejar claramente controles implementados y limites de alcance.
- Guardrails de exposicion externa documentados sin romper quickstart ni demos locales.
- CI y seguridad automatizada ahora reflejan el caso 02 como backend validado, no solo docker-build.

## v3.7.0 - 2026-04-02

### Added

- Caso 02 elevado a operacional con UI SRE, runbooks y nodos LangGraph adicionales.
- Frontend interactivo para el caso 02 con sugerencias y tracker de eventos.
- Rediseno del portal raiz hacia catalogo de automatizaciones IA.

## v3.6.0 - 2026-03-13

### Added

- Centro de APIs compartido para el portal y los casos operativos 01, 09, 10 y 13.
- Formulario de credenciales opcionales con nombre de variable, caso vinculado, enlace oficial y exportacion `.env` por caso.
- Guia documental explicita para instalar primero y completar APIs despues sin bloquear el modo DEMO.
