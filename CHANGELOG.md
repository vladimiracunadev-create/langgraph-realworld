# Changelog

Todos los cambios notables del repositorio se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

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
