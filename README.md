# LangGraph Realworld

[![CI](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/ci.yml)
[![Security Scan](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/langgraph-realworld/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.9.0-blue.svg)](CHANGELOG.md)

Portafolio de 25 casos de uso empresariales construidos con **LangGraph**, **FastAPI** y demos interactivas.
Cinco casos completamente operativos (01, 02, 09, 10 y 13); los restantes son scaffolds documentados y listos para ser elevados.

---

## Implementación Industrial — v3.9.0

El estándar actual del repositorio se apoya en estos pilares:

1. **Portal unificado** — `index.html` como entrada principal para navegar el portafolio.
2. **Casos de referencia reales** — backends FastAPI y UIs activas en los casos 01, 02, 09, 10 y 13.
3. **Estado tipado** — contratos explícitos de estado con `TypedDict` y flujos compatibles con LangGraph.
4. **Observabilidad** — endpoints `/health` y `/ready`, trazabilidad por eventos o `trace_id` según el caso.
5. **Modo dual** — demos offline y ruta clara para activar integraciones reales mediante `.env.example`.
6. **Operación portable** — ejecución por Docker, Hub CLI o entorno local según el caso.
7. **Hardening integrado** — workflows pinneados, baseline de secretos, auditoría de dependencias y Hub CLI seguro.
8. **Exposición externa opcional** — backends pueden exigir `X-Demo-Token` y aplicar `RATE_LIMIT_RPM`.
9. **Auditoría de seguridad por 8 capas** — contenedores non-root, puertos ligados a `127.0.0.1`, HTTP security headers, grype scan, Dependabot y detección de Trojan Source.

> [!TIP]
> Consulta el detalle técnico en [CHANGELOG.md](CHANGELOG.md), [SECURITY.md](SECURITY.md) y los docs en [`docs/`](docs/).

---

## Estado de los casos

### Casos operativos

| ID | Nombre | Estado | Stack principal |
|:---|:---|:---:|:---|
| **01** | [Soporte Cliente Omnicanal](cases/01-soporte-cliente-omnicanal/README.md) | `OPERATIVO` | FastAPI · LangGraph · Routing · DEMO/LIVE |
| **02** | [Mesa de Ayuda TI / SRE](cases/02-mesa-ayuda-ti-runbooks/README.md) | `OPERATIVO` | FastAPI · LangGraph · CMDB · HITL |
| **09** | [RRHH Screening & Agenda](cases/09-rrhh-screening-agenda/README.md) | `INDUSTRIAL` | FastAPI · LangGraph · MemorySaver · Resilience |
| **10** | [Onboarding de Empleados](cases/10-onboarding-empleados/README.md) | `INDUSTRIAL` | FastAPI · LangGraph · RBAC · Integrations |
| **13** | [Analista de Datos BI](cases/13-bi-analista-datos/README.md) | `INDUSTRIAL` | FastAPI · SQL Agent · Chart.js · DEMO/LLM |

### Casos scaffold (pendientes de implementación)

| ID | Nombre | Dominio |
|:---|:---|:---|
| 03 | [Incident Response SRE](cases/03-incident-response-sre/README.md) | SRE / Infraestructura |
| 04 | [SOC: Triage de Alertas](cases/04-soc-triage-alertas/README.md) | Seguridad / SOC |
| 05 | [Analista de Documentos](cases/05-analista-documentos/README.md) | Legal / Contratos |
| 06 | [Compliance & Auditorías](cases/06-compliance-auditorias/README.md) | Gobernanza |
| 07 | [Compras y Abastecimiento](cases/07-compras-abastecimiento/README.md) | Procurement |
| 08 | [Ventas B2B + CRM](cases/08-ventas-b2b-crm/README.md) | Comercial |
| 11 | [Tutor Adaptativo](cases/11-educacion-tutor-adaptativo/README.md) | Educación |
| 12 | [Psicometría y Evaluaciones](cases/12-psicometria-evaluaciones/README.md) | RRHH / Evaluación |
| 14 | [Finanzas: Conciliación](cases/14-finanzas-conciliacion/README.md) | Finanzas |
| 15 | [E-commerce Postventa](cases/15-ecommerce-postventa/README.md) | Comercio electrónico |
| 16 | [Planificador de Viajes](cases/16-viajes-planificador/README.md) | Travel |
| 17 | [Legal Intake](cases/17-legal-intake/README.md) | Legal |
| 18 | [Marketing con QA](cases/18-marketing-contenido-qa/README.md) | Marketing |
| 19 | [DevEx: PR Review](cases/19-devex-pr-review/README.md) | Ingeniería |
| 20 | [Migración Legacy](cases/20-migracion-legacy/README.md) | Arquitectura |
| 21 | [Documentación Automática](cases/21-docs-auto/README.md) | DevOps |
| 22 | [Backoffice: Automatización](cases/22-backoffice-automatizacion/README.md) | Operaciones |
| 23 | [Salud: Pre-triage](cases/23-salud-pretriage/README.md) | Salud |
| 24 | [Asistente PM](cases/24-pm-assistant/README.md) | Gestión de proyectos |
| 25 | [Supervisor + Workers](cases/25-supervisor-workers/README.md) | Multi-agente |

---

## Por dónde empezar

| Perfil | Ruta recomendada | Qué explorar |
|:---|:---|:---|
| Dev / DevOps | [Caso 01](cases/01-soporte-cliente-omnicanal/README.md) | Routing condicional y fallback DEMO/LIVE |
| IT Admin / SRE | [Caso 02](cases/02-mesa-ayuda-ti-runbooks/README.md) | Enriquecimiento de perfil, HITL y runbooks |
| Dev / ML Eng | [Caso 09](cases/09-rrhh-screening-agenda/README.md) | Resiliencia, streaming y MemorySaver |
| Dev / Arquitecto | [Caso 10](cases/10-onboarding-empleados/README.md) | RBAC, flujo empresarial e integraciones |
| Analista / BI | [Caso 13](cases/13-bi-analista-datos/README.md) | SQL seguro, visualización y LLM opcional |
| Recruiter / HM | [docs/RECRUITER.md](docs/RECRUITER.md) | Resumen ejecutivo y señales de seniority |
| Principiante | [docs/BEGINNERS_GUIDE.md](docs/BEGINNERS_GUIDE.md) | Mapa del repositorio paso a paso |
| Auditor / CISO | [SECURITY.md](SECURITY.md) | Postura de seguridad, controles y riesgos aceptados |

---

## Inicio rápido

```bash
# 1. Clonar
git clone https://github.com/vladimiracunadev-create/langgraph-realworld.git
cd langgraph-realworld

# 2. Copiar credenciales (opcional — los casos funcionan en DEMO sin ellas)
cp .env.example .env
# Editar .env con tu OPENAI_API_KEY

# 3. Levantar un caso con Docker
docker compose up case01

# 4. O usar el Hub CLI
python hub.py list
python hub.py run --case 01
```

---

## Activar APIs opcionales

- Copia `backend/.env.example` a `backend/.env` en el caso que quieras llevar a LIVE.
- O abre el portal raíz y usa **Configurar APIs del portfolio** para exportar el `.env` por caso.
- Sin credenciales, todos los casos funcionan en **DEMO** automáticamente.

### Perfil de exposición externa

Si un backend va a salir de `localhost`, activa controles adicionales en su `.env`:

```env
DEMO_AUTH_TOKEN=replace-with-a-long-random-token
RATE_LIMIT_RPM=60
TRUST_PROXY_HEADERS=false
```

> [!IMPORTANT]
> El portal sólo persiste valores si pulsas **Guardar localmente**. Los almacena en `localStorage` del navegador en texto claro. Úsalo sólo en equipos de confianza. Para trabajo serio, inyecta secretos vía `.env`, variables de entorno o un secret manager externo.

---

## Taxonomía de implementación

| Nivel | Criterios | Casos |
|:---|:---|:---|
| **OPERATIVO** | Backend real, DEMO/LIVE, CI, tests, hardening | 01, 02 |
| **INDUSTRIAL** | Backend real, streaming, observabilidad, docs completas | 09, 10, 13 |
| **SCAFFOLD** | Demo estática lista para evolucionar | 03–08, 11–12, 14–25 |

---

## Seguridad

Este repositorio ha sido auditado por 8 capas de seguridad (v3.9.0):
contenedores non-root, puertos vinculados a `127.0.0.1`, HTTP security headers en los 25 demos nginx,
imágenes Docker pineadas, grype scan en CI, Dependabot y detección de Trojan Source.

Consulta [SECURITY.md](SECURITY.md) para el detalle completo.
