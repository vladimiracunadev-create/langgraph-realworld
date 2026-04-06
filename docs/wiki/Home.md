# LangGraph Realworld — Wiki

[![CI](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml)
[![Security Scan](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml)
[![Version](https://img.shields.io/badge/version-3.9.0-blue.svg)](https://github.com/vladimiracunadev-create/langgraph-realworld/blob/main/CHANGELOG.md)

Portafolio de 25 casos de uso empresariales construidos con **LangGraph**, **FastAPI** y demos interactivas.
Cinco casos completamente operativos (01, 02, 09, 10 y 13); los restantes son scaffolds documentados y listos para elevarse.

---

## Implementación Industrial — v3.9.0

El estándar actual se apoya en estos pilares:

1. **Portal unificado** — `index.html` como entrada principal del portafolio.
2. **Casos de referencia reales** — backends FastAPI y UIs activas en los casos 01, 02, 09, 10 y 13.
3. **Estado tipado** — contratos explícitos con `TypedDict` y flujos compatibles con LangGraph.
4. **Observabilidad** — endpoints `/health` y `/ready`, trazabilidad por eventos o `trace_id`.
5. **Modo dual** — demos offline + ruta guiada para activar integraciones reales.
6. **Operación portable** — Docker, Hub CLI o entorno local.
7. **Hardening integrado** — workflows pinneados, baseline de secretos, auditoría de dependencias.
8. **Exposición externa opcional** — `X-Demo-Token` y `RATE_LIMIT_RPM` sin romper el quickstart.
9. **Auditoría de seguridad por 8 capas** — v3.9.0: non-root, `127.0.0.1`, HTTP headers, grype, Dependabot, Trojan Source.

---

## Estado de los casos

| ID | Nombre | Estado |
|:---|:---|:---:|
| 01 | Soporte Cliente Omnicanal | `OPERATIVO` |
| 02 | Mesa de Ayuda TI / SRE | `OPERATIVO` |
| 09 | RRHH Screening & Agenda | `INDUSTRIAL` |
| 10 | Onboarding de Empleados | `INDUSTRIAL` |
| 13 | Analista de Datos BI | `INDUSTRIAL` |
| 03–08, 11–12, 14–25 | Casos scaffold | `SCAFFOLD` |

---

## Por dónde empezar

| Perfil | Recurso |
|:---|:---|
| Dev / DevOps | [Caso 01](https://github.com/vladimiracunadev-create/langgraph-realworld/tree/main/cases/01-soporte-cliente-omnicanal) |
| IT Admin / SRE | [Caso 02](https://github.com/vladimiracunadev-create/langgraph-realworld/tree/main/cases/02-mesa-ayuda-ti-runbooks) |
| Analista / BI | [Caso 13](https://github.com/vladimiracunadev-create/langgraph-realworld/tree/main/cases/13-bi-analista-datos) |
| Auditor / CISO | [SECURITY.md](Security) |
| Contribuidor | [Guía de Contribución](Guia-de-Contribucion) |
| Principiante | [Guía para Principiantes](Guia-para-Principiantes) |

---

## Inicio rápido

```bash
git clone https://github.com/vladimiracunadev-create/langgraph-realworld.git
cd langgraph-realworld
docker compose up case01
# UI disponible en http://localhost:8001/web/
```

> [!IMPORTANT]
> Los casos funcionan en **DEMO** sin credenciales externas. Agrega `OPENAI_API_KEY` en `.env` para activar el modo **LIVE**.
