# Changelog

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
