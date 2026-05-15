# Changelog

## v4.11.0 - 2026-05-15

### Added

- Caso 12 — Psicometria y Evaluaciones elevado a OPERATIVO: 10 nodos LangGraph + 1 router (validez) con loop psicometrico (tope 2 iteraciones), helpers deterministas alpha de Cronbach, indice de dificultad (p / Likert), discriminacion item-total (Pearson corregido) y DIF entre grupos. Simulador de pilotaje Rasch-like dicotomico y modelo aditivo Likert con items inversos. 3 instrumentos DEMO: INST-COMP-DIG-01 (Competencias Digitales, dicotomico, n=40), INST-RAZ-LOG-02 (Razonamiento Logico, dicotomico, n=35, gatilla loop), INST-ESC-BIE-03 (Bienestar Laboral, Likert 5, n=50). Calibracion de baremos por percentiles, informes individuales con banda interpretativa, informe grupal con LLM opt-in (GPT-4o-mini). Puerto 8012.
- Suite de tests del caso 12: 29 tests (19 de grafo + 10 de API) todos en verde.
- Reemplazo del demo legacy nginx por backend real LangGraph + FastAPI con UI dark theme acento teal.

### Changed

- Total de backends operativos: 19 (incorpora caso 12 — 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 17, 19, 21, 25).
- Total de scaffolds: 6 (16, 18, 20, 22, 23, 24).
- Version bumped a 4.11.0 en README, ROADMAP, CHANGELOG, portal, docs y wiki.
- `docker-compose.yml` raiz: caso 12 movido de Nginx :9012 a backend :8012.

---

## v4.10.0 - 2026-05-11

### Added

- Caso 15 — E-commerce Postventa elevado a OPERATIVO: 11 nodos LangGraph + 3 routers (intencion · elegibilidad · stock) + nodo de convergencia derivar_humano, etiqueta de retorno con SHA-256 sobre payload canonicalizado, politica configurable (plazo 30d devolucion / 15d cambio, categorias bloqueadas, carrier), verificacion de stock real por SKU destino, 5 escenarios DEMO (ORD-001 seguimiento, ORD-002 devolucion elegible, ORD-003 vencida + categoria bloqueada, ORD-004 cambio con stock, ORD-005 cambio sin stock), respuesta empatica LIVE opt-in, puerto 8015.
- Suite de tests del caso 15: 33 tests (23 de grafo + 10 de API) todos en verde.
- Barrido profundo de documentacion: docs/ y docs/wiki/ sincronizados a v4.10.0 con la lista canonica de 18 operativos.

### Changed

- Total de backends operativos: 18 (01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 13, 14, 15, 17, 19, 21, 25).
- Total de scaffolds: 7 (12, 16, 18, 20, 22, 23, 24).
- Version bumped a 4.10.0 en README, ROADMAP, CHANGELOG, portal, docs y wiki.

---

## v4.9.0 - 2026-05-11

### Added

- Caso 11 — Tutor Adaptativo elevado a OPERATIVO: 10 nodos LangGraph + 3 routers (diagnostico · desempeno 3 vias · continuar/loop) con simulador IRT determinista por seed, escala habilidad 1.0–10.0, banco de 15 items de fracciones y porcentajes (dificultad 1.5–8.5), 3 estudiantes DEMO (STU-001 sin diagnostico, STU-002 nivel medio, STU-003 nivel bajo), politica configurable (deltas adaptacion, umbrales gap, tope sesion), perfil actualizado con metricas y recomendacion para proxima sesion, reporte ejecutivo LIVE opt-in, puerto 8011.
- Suite de tests del caso 11: 30 tests (22 de grafo + 8 de API) todos en verde.

### Changed

- Total de backends operativos: 17 (incorpora caso 11).
- Total de scaffolds: 8.
- Version bumped a 4.9.0.

---

## v4.8.0 - 2026-05-07

### Added

- Caso 07 — Compras y Abastecimiento elevado a OPERATIVO: 10 nodos LangGraph + router de politica de compras (umbral comite 25M CLP / no preferido 5M CLP), score multi-criterio determinista (precio 40 / plazo 30 / riesgo proveedor 30) con clamp 0-100, trazabilidad SHA-256 sobre OC, catalogo 9 proveedores homologados en 4 categorias, 3 escenarios DEMO (PR-001 oficina aprobada, PR-002 notebooks comparativa cerrada, PR-003 ingenieria escalada a comite), justificacion + resumen ejecutivo LIVE opt-in, puerto 8007.
- Suite de tests del caso 07: 25 tests (17 de grafo + 8 de API) todos en verde.
- docs/COSTS.md: inventario maestro de costos DEMO vs LIVE por caso y por escenario (lab personal, demo comercial, productivo enterprise).

### Changed

- Total de backends operativos: 16 (incorpora caso 07).
- Total de scaffolds: 9.
- Version bumped a 4.8.0.

---

## v4.7.0 - 2026-05-05

### Added

- Caso 21 — Documentacion Automatica elevado a OPERATIVO: 9 nodos LangGraph + router de calidad con loop condicional (tope 3 iter), outline adaptativo segun tipo de proyecto (api_rest / integration), redaccion 100% determinista desde artefactos del repo (endpoints, schemas, funciones, tests, changelog), QA por seccion con score 0-100 + penalizaciones configurables (endpoint sin doc, sin docstring, sin README, sin changelog, tests fallando, cobertura baja, sin CI), 3 escenarios DEMO (DOC-001 limpio score >=90, DOC-002 parcial, DOC-003 legacy con loop activo), publicacion Markdown completa + diff, puerto 8021.
- Suite de tests del caso 21: 25 tests (15 de grafo + 10 de API) todos en verde.

### Changed

- Total de backends operativos: 15 (01, 02, 03, 04, 05, 06, 08, 09, 10, 13, 14, 17, 19, 21, 25).
- Total de scaffolds: 10 (07, 11, 12, 15, 16, 18, 20, 22, 23, 24).
- Version bumped a 4.7.0 en README, docs, wiki, pyproject.toml y case.yml del caso 21.
- Ola 2 cerrada — proxima fase Ola 3.

---

## v4.6.0 - 2026-05-05

### Added

- Caso 06 — Compliance & Auditorias elevado a OPERATIVO: 8 nodos LangGraph + router de severidad, cadena de custodia SHA-256 encadenada (append-only) con seq + ts + accion + detalle + prev_hash + hash, 3 marcos regulatorios soportados (ISO 27001:2022, SOC 2 Type II, GDPR) con 4 controles cada uno, score de cumplimiento 0-100 con indicador verde/amarillo/rojo, 3 escenarios DEMO (AUD-001 ISO limpio, AUD-002 SOC 2 con faltantes, AUD-003 GDPR con ROPA y DPIA vencidas), validacion de evidencias por antiguedad y periodo, escalacion automatica por email a owners de controles con criticidad alta, puerto 8006.
- Suite de tests del caso 06: 26 tests (15 de grafo + 11 de API) todos en verde.
- Tooling opcional `uv` (Astral): scripts/uv-compile-all.sh, scripts/uv-install-case.sh, targets `make uv-bootstrap`, `make uv-compile`, `make uv-compile-check`, `make uv-install-case CASE=xx`. Guia completa en `docs/UV.md`. uv y pip/pip-tools coexisten sin conflicto — lockfiles intercambiables.

### Changed

- Total de backends operativos: 14.
- Total de scaffolds: 11.
- Version bumped a 4.6.0 en README, docs, wiki, pyproject.toml y case.yml del caso 06.

---

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
