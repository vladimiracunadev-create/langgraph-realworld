# Seguridad

> [!NOTE]
> **Version**: 4.0.0 | **Estado**: Auditado y endurecido | **Audiencia**: Auditores, CISO, Desarrolladores

Este repositorio esta pensado para exploracion tecnica, demos y validacion local de patrones LangGraph. La seguridad implementada busca reducir riesgos reales sin romper quickstart, `index.html`, Hub CLI ni los casos operativos 01, 02, 03, 09, 10, 13, 19 y 25.

---

## Resultado de la auditoria de seguridad (v4.0.0)

### Capa 1 — Contenedor y proceso

| Control | Estado |
|---|---|
| Proceso no-root en backends 01, 02, 03 | **RESUELTO** — `groupadd/useradd appuser` + `USER appuser` agregados |
| Proceso no-root en backends 09, 10, 13, 19, 25 | OK — ya tenia `USER appuser` |
| Proceso no-root en demos nginx (25 casos) | **RESUELTO** — `USER nginx` + chown de directorios en todos los demos |
| Imagen Python pineada a version exacta | **RESUELTO** — `python:3.11.10-slim` en backends 01, 02, 03, 13, 19, 25 (09 ya tenia 3.11.10) |
| Imagen nginx pineada a version exacta | **RESUELTO** — `nginx:1.27.3-alpine` en los 25 demos |
| Healthcheck con herramienta disponible | **RESUELTO** — demos usan `wget --spider` (BusyBox, incluido en Alpine); backends usan `curl` (instalado explicitamente) |
| Directorios de log/PID accesibles por usuario no-root | OK — `chown` antes de `USER` en todos los Dockerfiles |

### Capa 2 — Red y exposicion de puertos

| Control | Estado |
|---|---|
| Puertos de docker-compose vinculados a 127.0.0.1 | **RESUELTO** — todos los puertos usan `127.0.0.1:XXXX:XXXX` |

### Capa 3 — Credenciales y variables de entorno

| Control | Estado |
|---|---|
| Variables criticas sin fallback hardcodeado | OK — `OPENAI_API_KEY` sin fallback; si no esta definida la llamada a la API falla con error claro |
| `.env` en `.gitignore` | OK |
| `.env.example` commiteado y fuera de `.gitignore` | OK |
| Lock files para aplicaciones | PENDIENTE — ver seccion de riesgos aceptados |

### Capa 4 — Servidor web

| Control | Estado |
|---|---|
| HTTP security headers en los 25 demos nginx | **RESUELTO** — `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Content-Security-Policy`, `Permissions-Policy` en todos los nginx.conf |
| Listado de directorios | OK — nginx no lista directorios por defecto |
| `display_errors` PHP | N/A — el stack no usa PHP |

### Capa 5 — Herramientas con acceso a datos sensibles

| Control | Estado |
|---|---|
| SQL solo lectura (caso 13) | OK — SELECT/CTE unicamente, conexion SQLite read-only, limite de filas |
| Hub CLI sin shell injection | OK — sin `shell=True`, allowlist de ejecutables, bloqueo de metacaracteres |
| CSRF | OK — APIs JSON con CORS allowlist; CSRF clasico no aplica a APIs REST sin cookies de sesion |
| Rate limiting | OK — opt-in via `RATE_LIMIT_RPM` |
| Whitelist de destinos | OK — CORS allowlist + validacion de parametros de entrada |

### Capa 6 — Autenticacion

| Control | Estado |
|---|---|
| Capa de autenticacion | RIESGO ACEPTADO — opt-in via `DEMO_AUTH_TOKEN`. Ver recomendaciones operativas. |

### Capa 7 — Pipeline CI/CD

| Control | Estado |
|---|---|
| Escaneo de secretos | OK — `detect-secrets` con baseline versionada |
| Auditoria de dependencias | OK — `pip-audit` sobre todos los `requirements.txt` |
| Escaneo de imagenes Docker | **RESUELTO** — `grype` (Anchore) para los 5 backends con imagen. Se eligio grype sobre Trivy por el incidente de supply chain que afecto a Trivy; la action esta pineada a SHA de commit. |
| Dependabot | **RESUELTO** — `.github/dependabot.yml` con cobertura de GitHub Actions, pip (raiz + 5 backends) y Docker |
| Actions pineadas por SHA | OK — todos los `uses:` con commit SHA |
| Permisos minimos por job | OK — `contents: read` por defecto |
| CodeQL | OK — Python, `security-extended` + `security-and-quality` |

### Capa 8 — Cadena de suministro

| Control | Estado |
|---|---|
| Line endings LF en shell scripts | OK — `.gitattributes` con `*.sh text eol=lf` y `Dockerfile* text eol=lf` |
| Deteccion de Unicode bidi (CVE-2021-42574) | **RESUELTO** — job `supply_chain` en `security.yml` detecta caracteres de control bidi |
| Deteccion de patrones de ofuscacion | **RESUELTO** — job `supply_chain` detecta `exec+base64`, `eval()` dinamico, `os.system` con concatenacion |

---

## Controles implementados (historico)

### Nuevos controles en v4.0.0

- Tres nuevos backends operativos elevados: casos 03 (Incident Response SRE), 19 (DevEx PR Review) y 25 (Supervisor + Workers).
- OAuth2/OIDC opt-in via `USE_OAUTH2=true` en todos los backends operativos.
- Observabilidad extendida: `/metrics` por servicio con latencia, errores y modo DEMO/LIVE; logging JSON estructurado con `trace_id`.
- LangSmith opt-in para trazabilidad de agentes en produccion.
- Reverse proxy nginx + TLS para exposicion segura con rate limiting y security headers.
- Jobs CI dedicados para los casos 03, 19 y 25 (Python checks + pytest).
- pip-compile lock files deterministas para todos los backends operativos.
- grype con `fail-build: true` para 8 backends.

### GitHub Actions y CI/CD (v3.8.0+)

- Actions pinneadas por commit SHA en `ci.yml`, `security.yml` y `wiki-sync.yml`.
- Permisos minimos por workflow/job (`contents: read` por defecto; `security-events: write` solo para CodeQL; `contents: write` solo para wiki sync).
- `CodeQL` activo para Python con consultas `security-extended` y `security-and-quality`.
- Escaneo de secretos en CI con `detect-secrets` y baseline versionada.
- Escaneo de dependencias Python con `pip-audit` sobre `requirements.txt` raiz y de los casos.
- Modo gradual para dependencias: `soft` en PR, `hard` en `main`, `schedule` y `workflow_dispatch`.
- Los casos 02, 03, 09, 13, 19 y 25 tienen suite propia y job dedicado en CI.

### Secretos y configuracion

- `.env.example` mas explicitos sobre DEMO vs LIVE y sobre no commitear credenciales reales.
- El portal ya no persiste valores implicitamente al copiar o descargar; solo guarda si pulsas `Guardar localmente`.
- Los casos con CORS configurable usan allowlists locales por defecto, no `*` abierto para navegadores externos.

### Exposicion externa opcional

- Los casos 01, 02, 03, 09, 10, 13, 19 y 25 aceptan `DEMO_AUTH_TOKEN` para exigir el header `X-Demo-Token` en sus endpoints operativos.
- Los mismos casos aceptan `RATE_LIMIT_RPM` para aplicar rate limiting en memoria por cliente.
- `TRUST_PROXY_HEADERS=false` por defecto evita confiar en `X-Forwarded-For` salvo despliegue detras de un proxy controlado.

### Agentes, tools y LLMs

- `hub.py` no usa `shell=True` para ejecutar `case.yml`.
- `hub.py` restringe ejecutables permitidos (`python`, `uvicorn`, `docker compose`) y bloquea metacaracteres de shell, `python -c` y rutas fuera del caso.
- Caso 13 endurecido como SQL read-only.
- Endpoints con validacion adicional de `thread_id`, `ticket_id`, `employee_id` o `question`.

---

## Riesgos aceptados y pendientes

| Riesgo | Decision | Solucion propuesta si se necesita |
|---|---|---|
| Sin lock files de dependencias Python | Aceptado para demo — `requirements.txt` sin pinning exacto | Adoptar `pip-compile` (pip-tools) o Poetry y commitear el lock file |
| Autenticacion opt-in | Aceptado para demo local | Activar `DEMO_AUTH_TOKEN` + TLS + proxy antes de exponer en red compartida |
| Rate limiting en memoria | Aceptado para demo | Reemplazar con rate limiting en proxy/API gateway para Internet abierta |
| Prompt injection completa | Parcialmente mitigado | Sandbox de agentes y validacion de contenido de usuario |

---

## Amenazas mitigadas

- Acceso desde otras maquinas de la red local a puertos de backend/portal
- Clickjacking y MIME sniffing en demos (security headers)
- Proceso con privilegios root en todos los contenedores
- Contenedores con imagen base no reproducible (tags flotantes)
- Healthcheck con binario ausente que fallaba silenciosamente
- Dependencias con CVE conocidos sin notificacion automatica (Dependabot + pip-audit)
- Supply chain via Trojan Source (bidi detection en CI)
- Ofuscacion base64/eval en commits
- Imagenes Docker con vulnerabilidades criticas (grype scan en CI)
- Ejecucion arbitraria desde `case.yml` o Hub CLI
- Filtracion de secretos en archivos versionados

---

## Recomendaciones operativas

- Usa secretos de menor privilegio posible y rotalos despues de demos externas.
- Si necesitas exponer un caso fuera de localhost, activa `DEMO_AUTH_TOKEN`, `RATE_LIMIT_RPM`, TLS y un proxy seguro antes de abrirlo.
- Revisa los findings de `pip-audit` antes de promover cambios a `main`.
- Revisa los findings de `grype` en PRs — `fail-build: false` en modo suave, escalar a `true` antes de produccion real.
- Manten `ALLOWED_ORIGINS` acotado a los hosts realmente usados.

---

## Reporte de vulnerabilidades

Si detectas una vulnerabilidad en este repositorio:

1. Abre un Issue con la etiqueta `security` si el hallazgo es apto para disclosure publico.
2. Si el hallazgo expone credenciales, ejecucion remota o datos sensibles reales, evita publicarlo con detalle y coordina el reporte privado con el mantenedor.

---

## Limites de la documentacion

Este `SECURITY.md` describe la postura actual del repositorio, no una certificacion formal ni una garantia de seguridad total. La prioridad es seguridad realista y compatible con una experiencia de exploracion local de IA aplicada.
