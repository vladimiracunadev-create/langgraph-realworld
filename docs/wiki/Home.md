# LangGraph Realworld — Wiki

[![CI](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml)
[![Security Scan](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml)
[![Version](https://img.shields.io/badge/version-4.7.0-blue.svg)](https://github.com/vladimiracunadev-create/langgraph-realworld/blob/main/CHANGELOG.md)

Portafolio de 25 casos de uso empresariales construidos con **LangGraph** y **FastAPI**.
**15 backends completamente operativos** (01, 02, 03, 04, 05, 06, 08, 09, 10, 13, 14, 17, 19, 21 y 25) con streaming, OAuth2/OIDC opt-in, observabilidad LangSmith, `/metrics` por servicio, logging JSON estructurado y reverse proxy nginx + TLS.
Los 10 casos restantes son scaffolds documentados listos para elevar al siguiente nivel.

---

## Implementacion Industrial — v4.7.0

| # | Pilar | Descripcion |
|:-:|:---|:---|
| 1 | Portal unificado | `index.html` como entrada principal del portfolio |
| 2 | Casos de referencia reales | Backends FastAPI y UIs activas en los casos 01, 02, 03, 04, 05, 06, 08, 09, 10, 13, 14, 17, 19, 21 y 25 |
| 3 | Estado tipado | Contratos explicitos con TypedDict y flujos compatibles con LangGraph |
| 4 | Observabilidad | /health, /ready, /metrics con latencia, errores y modo; LangSmith opt-in |
| 5 | Modo dual | DEMO offline + ruta clara para activar integraciones reales |
| 6 | Operacion portable | Docker, nginx+TLS, Hub CLI o entorno local segun el caso |
| 7 | Hardening integrado | grype fail-build, detect-secrets history, pip-compile, Dependabot |
| 8 | Auth multicapa | X-Demo-Token (opt-in) + OAuth2/OIDC JWT (opt-in via USE_OAUTH2=true) |
| 9 | Auditoria 8 capas | Non-root, 127.0.0.1, HTTP headers, grype, Trojan Source, nginx TLS |

---

## Estado de los casos

### Operativos e industriales (15)

| ID | Nombre | Nivel | UI web |
|:---:|:---|:---:|:---:|
| 01 | Soporte Cliente Omnicanal | OPERATIVO | Si |
| 02 | Mesa de Ayuda TI / SRE | OPERATIVO | Si |
| 03 | Incident Response SRE | OPERATIVO | Si |
| 04 | SOC Triage de Alertas | OPERATIVO | Si |
| 05 | Analista de Documentos | OPERATIVO | Si |
| 06 | Compliance & Auditorías | OPERATIVO | Si |
| 08 | Ventas B2B + CRM | OPERATIVO | Si |
| 09 | RRHH Screening & Agenda | INDUSTRIAL | Si |
| 10 | Onboarding de Empleados | INDUSTRIAL | Si |
| 13 | Analista de Datos BI | INDUSTRIAL | Si |
| 14 | Finanzas — Conciliación | OPERATIVO | Si |
| 17 | Legal Intake | OPERATIVO | Si |
| 19 | DevEx: PR Review | OPERATIVO | Si |
| 21 | Documentación Automática | OPERATIVO | Si |
| 25 | Supervisor + Workers | OPERATIVO | Si |

### Scaffold (10)

Casos 07, 11, 12, 15, 16, 18, 20, 22, 23, 24 — scaffolds documentados con README y Mermaid listos para elevar.
Orden de prioridad en el [Roadmap](Roadmap).

---

## Inicio rapido

```bash
git clone https://github.com/vladimiracunadev-create/langgraph-realworld.git
cd langgraph-realworld

# Levantar un caso con Docker (funciona sin API keys en DEMO)
docker compose up case01
# UI en http://localhost:8001/web/

# O usar el Hub CLI
python hub.py list
python hub.py run --case 01
```

> Los casos funcionan en **DEMO** sin credenciales. Agrega `OPENAI_API_KEY` en `.env` para modo **LIVE**.

---

Para mas detalle, ver el [repositorio en GitHub](https://github.com/vladimiracunadev-create/langgraph-realworld).
