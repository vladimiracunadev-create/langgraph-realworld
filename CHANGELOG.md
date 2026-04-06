# Changelog

## v3.8.0 - 2026-04-06

### Added

- Fase 2 de hardening aplicada a los casos operativos con `DEMO_AUTH_TOKEN`, `RATE_LIMIT_RPM` y `TRUST_PROXY_HEADERS` como guardrails opcionales de exposicion externa.
- Suite propia para el caso 02 (`pytest`) con validacion de API, auth opcional, rate limiting y flujo LangGraph.
- Job dedicado en CI para el caso 02.

### Changed

- README, docs, wiki local, casos clave y Hub CLI sincronizados a `v3.8.0`.
- Documentacion reescrita en ASCII para reducir drift y problemas de codificacion.
- `hub.py` y la documentacion del Hub alineados con la taxonomia `Operational/Industrial (v3.8.0)`.

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
