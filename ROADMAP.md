# Hoja de Ruta

> **Versión**: 4.15.0 | **Estado**: Industrial | **Rama principal**: `main`

El estándar técnico del repositorio ya está definido. Antes de crear o modificar un caso, leer el skill directamente — no se rediseña lo que ya existe:

- Crear / elevar un caso → [`.agents/skills/crear_caso/SKILL.md`](.agents/skills/crear_caso/SKILL.md)
- Actualizar documentación → [`.agents/skills/actualizar_doc/SKILL.md`](.agents/skills/actualizar_doc/SKILL.md)
- Auditar un caso existente → [`.agents/skills/validar_caso/SKILL.md`](.agents/skills/validar_caso/SKILL.md)

---

## Estado de los 25 casos

### Operativos e industriales (25)

| ID | Caso | Nivel | UI web | Integraciones LIVE |
|:---:|:---|:---:|:---:|:---|
| 01 | [Soporte Cliente Omnicanal](cases/01-soporte-cliente-omnicanal/README.md) | OPERATIVO | ✅ | LLM opt-in (OpenAI) |
| 02 | [Mesa de Ayuda TI / SRE](cases/02-mesa-ayuda-ti-runbooks/README.md) | OPERATIVO | ✅ | CMDB, runbooks (DEMO) |
| 03 | [Incident Response SRE](cases/03-incident-response-sre/README.md) | OPERATIVO | ✅ | PagerDuty, Datadog (DEMO) |
| 04 | [SOC Triage de Alertas](cases/04-soc-triage-alertas/README.md) | OPERATIVO | ✅ | VirusTotal, AbuseIPDB, SIEM (DEMO) |
| 05 | [Analista de Documentos](cases/05-analista-documentos/README.md) | OPERATIVO | ✅ | PDF/DOCX opt-in, LLM opt-in (OpenAI) |
| 06 | [Compliance & Auditorías](cases/06-compliance-auditorias/README.md) | OPERATIVO | ✅ | LLM opt-in, ISO 27001/SOC 2/GDPR, cadena de custodia SHA-256 |
| 07 | [Compras y Abastecimiento](cases/07-compras-abastecimiento/README.md) | OPERATIVO | ✅ | LLM opt-in, score multi-criterio, router política comité, OC SHA-256 |
| 08 | [Ventas B2B + CRM](cases/08-ventas-b2b-crm/README.md) | OPERATIVO | ✅ | LLM opt-in, ICP scoring, 4 cuentas DEMO |
| 09 | [RRHH Screening & Agenda](cases/09-rrhh-screening-agenda/README.md) | INDUSTRIAL | ✅ | LLM + MemorySaver |
| 10 | [Onboarding de Empleados](cases/10-onboarding-empleados/README.md) | INDUSTRIAL | ✅ | HRIS, IAM, Slack (DEMO) |
| 11 | [Tutor Adaptativo](cases/11-educacion-tutor-adaptativo/README.md) | OPERATIVO | ✅ | LLM opt-in, simulador IRT determinista, banco 15 ítems |
| 12 | [Psicometría y Evaluaciones](cases/12-psicometria-evaluaciones/README.md) | OPERATIVO | ✅ | LLM opt-in, α Cronbach, discriminación item-total, DIF entre grupos, loop validez |
| 13 | [Analista de Datos BI](cases/13-bi-analista-datos/README.md) | INDUSTRIAL | ✅ | SQL + Chart.js + LLM opt-in |
| 14 | [Finanzas: Conciliación](cases/14-finanzas-conciliacion/README.md) | OPERATIVO | ✅ | LLM opt-in, z-score outliers, 3 escenarios DEMO |
| 15 | [E-commerce Postventa](cases/15-ecommerce-postventa/README.md) | OPERATIVO | ✅ | LLM opt-in, 3 routers (intención · elegibilidad · stock), etiqueta SHA-256, 5 escenarios DEMO |
| 16 | [Planificador de Viajes](cases/16-viajes-planificador/README.md) | OPERATIVO | ✅ | LLM opt-in, itinerario multi-criterio, escenarios DEMO travel |
| 17 | [Legal Intake](cases/17-legal-intake/README.md) | OPERATIVO | ✅ | LLM opt-in (OpenAI), 3 especialidades, 3 plantillas |
| 18 | [Marketing con QA](cases/18-marketing-contenido-qa/README.md) | OPERATIVO | ✅ | LLM opt-in, doble loop QA (estilo + hechos), fact-check con 6 fuentes |
| 19 | [DevEx: PR Review](cases/19-devex-pr-review/README.md) | OPERATIVO | ✅ | GitHub API (DEMO) |
| 20 | [Migración Legacy](cases/20-migracion-legacy/README.md) | OPERATIVO | ✅ | LLM opt-in, inventario, dependencias, plan de migración multi-fase |
| 21 | [Documentación Automática](cases/21-docs-auto/README.md) | OPERATIVO | ✅ | LLM opt-in, outline adaptativo, loop QA |
| 22 | [Backoffice Automatización](cases/22-backoffice-automatizacion/README.md) | OPERATIVO | ✅ | LLM opt-in (resumen), 3 routers, loop completitud, cadena de custodia SHA-256, 4 solicitudes DEMO |
| 23 | [Salud: Pre-triage](cases/23-salud-pretriage/README.md) | OPERATIVO | ✅ | LLM opt-in, triage clínico determinista, routers de severidad |
| 24 | [Asistente PM](cases/24-pm-assistant/README.md) | OPERATIVO | ✅ | LLM opt-in, backlog, riesgos, reportes ejecutivos |
| 25 | [Supervisor + Workers](cases/25-supervisor-workers/README.md) | OPERATIVO | ✅ | 4 workers especializados (DEMO) |

### Scaffold — listos para elevar (0)

> Ola 3 cerrada en v4.14.0. Todos los casos del portfolio están en nivel OPERATIVO o INDUSTRIAL.

---

## Orden de elevación de casos

```
SCAFFOLD  →  (seguir SKILL.md)  →  OPERATIVO  →  (observabilidad + hardening)  →  INDUSTRIAL
```

### Ola 1 — Alta prioridad

| Caso | Por qué | Núcleo LangGraph |
|:---|:---|:---|
| ~~**04 — SOC Triage**~~ | ✅ **COMPLETADO v4.1.0** — Router de riesgo (3 vías), threat intel, SIEM context | Router por score, 2 routers condicionales, stubs LIVE |
| ~~**05 — Analista de Documentos**~~ | ✅ **COMPLETADO v4.2.0** — Pipeline contractual, 7 nodos, router de riesgo, 3 docs DEMO | Pipeline secuencial, router condicional, keyword extraction, LLM opt-in |
| ~~**17 — Legal Intake**~~ | ✅ **COMPLETADO v4.3.0** — Intake + clasificación + 3 especialidades + 3 plantillas + asignación de abogado | 10 nodos, 2 routers (especialidad / completitud), MemorySaver, LLM opt-in |

### Ola 2 — Impacto comercial

| Caso | Por qué |
|:---|:---|
| ~~**08 — Ventas B2B + CRM**~~ | ✅ **COMPLETADO v4.4.0** — Pipeline outbound: ICP scoring, outreach por industria, CRM stage automático | 10 nodos, 2 routers (ICP / señal), 4 cuentas DEMO, asignación de AE |
| ~~**14 — Finanzas: Conciliación**~~ | ✅ **COMPLETADO v4.5.0** — Cierre mensual: matching multi-criterio, detección z-score, 3 tipos de discrepancia, indicador verde/amarillo/rojo | 9 nodos, 3 escenarios DEMO, sin dependencias numéricas externas |
| ~~**06 — Compliance**~~ | ✅ **COMPLETADO v4.6.0** — Preparación de auditoría ISO 27001/SOC 2/GDPR: mapeo de controles, recopilación, escalación, validación, cadena de custodia SHA-256 encadenada (append-only) | 8 nodos, 1 router de severidad, 3 escenarios DEMO, hash chain inmutable |
| ~~**21 — Docs Automática**~~ | ✅ **COMPLETADO v4.7.0** — Pipeline LangGraph con loop QA condicional: escaneo de repo, extracción de artefactos, outline adaptativo, redacción determinista, score por sección, revisión iterativa (tope 3), publicación Markdown | 9 nodos, router + loop QA, 3 escenarios DEMO |

### Ola 3 — Dominio especializado

| Caso | Por qué | Núcleo LangGraph |
|:---|:---|:---|
| ~~**07 — Compras y Abastecimiento**~~ | ✅ **COMPLETADO v4.8.0** — Pipeline procurement: validación PR → catálogo homologado → RFQs → cotizaciones → score multi-criterio (precio 40 / plazo 30 / riesgo 30) → router política (umbral comité 25M / no preferido 5M) → recomendación → aprobación → OC con SHA-256 | 10 nodos, 1 router (política), 3 escenarios DEMO, OC con hash inmutable |
| ~~**11 — Tutor Adaptativo**~~ | ✅ **COMPLETADO v4.9.0** — Tutoría personalizada IRT: diagnóstico inicial (3 ítems), selección adaptativa por gap habilidad‑dificultad, router de desempeño 3 vías (dominio / remediación / frustración) con loop hasta tope, perfil actualizado y reporte ejecutivo | 10 nodos, 3 routers (diagnóstico / desempeño / continuar), 3 estudiantes DEMO, banco 15 ítems, simulador determinista por seed |
| ~~**15 — E-commerce Postventa**~~ | ✅ **COMPLETADO v4.10.0** — Postventa para e-commerce: lookup OMS → clasificación intención → 3 caminos (tracking · devolución con elegibilidad · cambio con stock) → convergencia humano o resolución automática → respuesta empática + resumen | 11 nodos, 3 routers (intención / elegibilidad / stock), etiqueta retorno con SHA-256, 5 escenarios DEMO |
| ~~**12 — Psicometría y Evaluaciones**~~ | ✅ **COMPLETADO v4.11.0** — Validación psicométrica de instrumentos: revisión experta → ensamblar → pilotaje simulado → análisis (α Cronbach, dificultad, discriminación item-total, DIF entre grupos) → router validez con loop tope → calibración baremos → informes individuales con percentil y banda → informe grupal ejecutivo | 10 nodos, 1 router (validez) + loop, 3 instrumentos DEMO (2 dicotómicos + 1 Likert), 29 tests |

| ~~**18 — Marketing con QA**~~ | ✅ **COMPLETADO v4.12.0** — Pipeline marketing con doble loop QA: parseo de brief → borrador → revisión estilo de marca (tope 2 iter, palabras prohibidas / no preferidas / frases largas) → verificación de hechos (tope 2 iter, fact-check contra 6 fuentes, alucinaciones retiradas) → optimización SEO → aprobación editor (score ponderado hechos 0.5 / estilo 0.3 / SEO 0.2) → publicación → resumen | 10 nodos, 2 routers + 2 loops, 3 briefs DEMO (blog · email · landing), 28 tests |

| ~~**22 — Backoffice Automatización**~~ | ✅ **COMPLETADO v4.13.0** — Pipeline ops: parseo de solicitud → clasificación contra catálogo de operaciones → verificación identidad/permisos → router permisos (rechaza o avanza) → validación de completitud con loop (tope 2 iter, autocompletado DEMO) → ejecución simulada en sistema destino (CRM/HRIS/BI) → router resultado (escalar soporte o confirmar) → log inmutable encadenado SHA-256 sobre todos los eventos | 11 nodos, 3 routers + 1 loop, 4 solicitudes DEMO (exitosa · loop · rechazo · escalada), 33 tests |
| ~~**16 — Planificador de Viajes**~~ | ✅ **COMPLETADO v4.14.0** — Pipeline travel: parseo de requerimiento → búsqueda de opciones (vuelos · hospedaje · actividades) → score multi-criterio (precio · duración · calificación) → armado de itinerario → resumen ejecutivo. Puerto 8016. |
| ~~**20 — Migración Legacy**~~ | ✅ **COMPLETADO v4.14.0** — Pipeline arquitectura: inventario de sistema legacy → análisis de dependencias → plan de migración multi-fase → estimación de riesgo → reporte ejecutivo. Puerto 8020. |
| ~~**23 — Salud: Pre-triage**~~ | ✅ **COMPLETADO v4.14.0** — Pipeline clínico: ingesta de síntomas → clasificación de severidad → router triage (urgente · ambulatorio · auto-cuidado) → recomendaciones + disclaimer médico. Puerto 8023. |
| ~~**24 — Asistente PM**~~ | ✅ **COMPLETADO v4.14.0** — Pipeline gestión: ingesta de backlog → identificación de riesgos → priorización multi-criterio → reporte ejecutivo para stakeholders. Puerto 8024. |

Ola 3 cerrada en v4.14.0 — portfolio al 100% (25/25 operativos).

---

## Mantenimiento v4.15.0

Release de hardening de seguridad y mantenibilidad — sin nuevos casos. Resultado
de la auditoría adversarial v4.14.0 (4 PRs mergeados: #63, #64, #65, #66).

| PR | Item | Cambio |
|:---:|:---|:---|
| #63 | CRIT-1..4 | JWKS cache TTL 300s, `aud`/`iss` obligatorios cuando `USE_OAUTH2=true`, HTTP 500 sanitizado (`"Internal server error"` + `logger.exception()`), `pr_id` con `pattern=SAFE_ID_PATTERN` en caso 19, 401 OAuth2 sin filtrar `exc` |
| #64 | CI expansion | Tests Python expandidos de 10 → 25 casos (matrix único); `container_scan` grype expandido de 9 → 25 casos |
| #65 | shared/ extraction | `shared/lgrw_common/auth.py` + `settings.py` = fuente canónica; `scripts/sync_shared.py` propaga a `cases/*/backend/src/`; CI bloquea drift con `--check` |
| #66 | jose → joserfc | `python-jose+ecdsa` (abandonada, side-channel timing) reemplazada por `joserfc 1.6.5` en los 25 casos; requirements regenerados |

Detalle completo en [CHANGELOG.md](CHANGELOG.md#v4150--2026-05-19) y
[SECURITY.md](SECURITY.md#hardening-v4150).

---

## Mejoras transversales pendientes

### v4.1.0 — SOC Triage operativo + integraciones reales

**Completado**: Caso 04 elevado a OPERATIVO — 8 nodos, 2 routers, stubs VirusTotal/SIEM/Ticketing.

**Integraciones reales pendientes en casos existentes**:

| Caso | Integración pendiente | Variable de entorno |
|:---:|:---|:---|
| [03](cases/03-incident-response-sre/README.md) | PagerDuty + Datadog reales | `PAGERDUTY_TOKEN`, `DATADOG_API_KEY` |
| [04](cases/04-soc-triage-alertas/README.md) | VirusTotal + AbuseIPDB + Splunk/Elastic reales | `VIRUSTOTAL_API_KEY`, `SPLUNK_TOKEN` |
| [10](cases/10-onboarding-empleados/README.md) | HRIS, IAM, Slack, correo (4 `TODO REAL`) | Por `.env` del caso |
| [19](cases/19-devex-pr-review/README.md) | GitHub API real | `GITHUB_TOKEN` |
| [25](cases/25-supervisor-workers/README.md) | APIs financieras/legales reales | Por definir |

### Elevación OPERATIVO → INDUSTRIAL (casos 03, 19, 25)

- [ ] `compose.smoke.yml` con smoke tests en Docker
- [ ] Tests de integración con `stream_mode` verificado
- [ ] Logging JSON estructurado con `ContextVar` + `TraceIdFilter` (como casos 09/10)
- [ ] OAuth2/OIDC opt-in confirmado en tests
- [ ] `/metrics` documentado en README del caso

### Largo plazo

- Kubernetes con `NetworkPolicy` y `SecurityContext` completos
- IaC (Terraform / Pulumi) para entornos reproducibles en cloud
- OpenTelemetry para trazas distribuidas entre servicios
- Secret manager externo (Vault, AWS Secrets Manager)

---

## Criterios de madurez

```
SCAFFOLD   → README con Mermaid + case.yml + estructura de carpetas base
                 ↓  seguir .agents/skills/crear_caso/SKILL.md
OPERATIVO  → backend real + interfaz web + DEMO/LIVE + Docker + tests + docs
                 ↓  streaming verificado + observabilidad + hardening completo
INDUSTRIAL → todo lo de OPERATIVO + compose.smoke + logging JSON estructurado
             + /metrics documentado + OAuth2 verificado en tests + docs operativas completas
```

---

## Pendientes técnicos para v4.16+

Backlog identificado durante la auditoría adversarial v4.14.0 y la implementación
v4.15.0. Ordenado por prioridad declarada (no asignada).

### Alta

1. **Migrar `shared/lgrw_common/` a paquete pip-instalable real** y cambiar el
   build context de los 25 Dockerfile a la raíz del repo. Esto elimina por
   completo la duplicación de `auth.py` y `settings.py` en `cases/*/backend/src/`
   (hoy se mantienen sincronizadas vía script + CI, no por import real). Riesgo:
   tocar 25 Dockerfile + 25 compose.yml simultáneamente.
2. **Reemplazar `MemorySaver` de LangGraph** en producción por `SqliteSaver` o
   `PostgresSaver` con TTL. Hoy 24/25 casos guardan estado de threads en RAM →
   leak garantizado con `thread_id` controlado por cliente.
3. **`rate_limit_buckets` con eviction**: hoy es un `dict` simple sin límite →
   memory leak por cada IP única que acceda a `/api/`. Migrar a
   `cachetools.TTLCache(maxsize=10000, ttl=120)`.
4. **Mover `/metrics`, `/health`, `/ready` bajo `/api/` o protegerlos** con un
   token separado. Hoy exponen modo (DEMO/LIVE), uptime, error rate, y en
   algunos casos paths absolutos (caso 13 `/ready` filtra `settings.database_path`).
   Total expuesto: ~150 endpoints públicos × 6 paths × 25 backends.

### Media

5. **Reemplazar `_metrics` dict global con `+=` por `prometheus_client.Counter`**:
   thread-safe + formato Prometheus estándar (vs. el JSON custom actual). Mejora
   adopción con stacks observabilidad estándar.
6. **`DATA_DIR` con validación de path** (anti path-traversal). Hoy un env var
   malicioso `DATA_DIR=../../etc` resultaría en lectura fuera del directorio
   esperado.
7. **Sanitización de prompt injection** en campos free-text que van directo al
   LLM en modo LIVE (caso 01 `ticket.message`, caso 13 `question`).
8. **Pin de SHA del digest de `python:3.11-slim`** y eliminar `apt-get upgrade -y`
   de los 25 Dockerfile (no determinista).

### Baja

9. **Cobertura de tests medida con `--cov`** en CI (hoy: tests pasan/fallan, sin
   métrica de cobertura por caso).
10. **Consolidar `requirements.in` para los 3 casos sin él** (11, 12, 15) y
    estandarizar el flujo pip-compile en los 25.
11. **Migrar `dependabot` a `renovate`** o ajustar dependabot a abrir 1 PR
    consolidado por bump (hoy: 1 PR × 25 casos × cada bump = ruido).
12. **`audit_links.sh` sin trackear** en la raíz (script untracked desde sesiones
    anteriores). Decidir si commitear o agregar a `.gitignore`.
