# Seguridad

> [!NOTE]
> **Version**: 3.9.0 | **Estado**: Endurecido para demo/local y exposicion externa controlada | **Audiencia**: Auditores, CISO, Desarrolladores

Este repositorio esta pensado para exploracion tecnica, demos y validacion local de patrones LangGraph. La seguridad implementada busca reducir riesgos reales sin romper quickstart, `index.html`, Hub CLI ni los casos operativos 01, 02, 09, 10 y 13.

---

## Modelo operativo real

- Los casos estan disenados para correr en modo DEMO cuando faltan credenciales reales.
- El portal raiz ayuda a generar `.env`, pero no reemplaza un secret manager empresarial.
- El repositorio no debe exponerse a Internet como plataforma multi-tenant sin una capa adicional de proxy, observabilidad y gobierno.
- Fase 2 agrega un perfil opcional de exposicion externa con token y rate limiting para los backends operativos.

---

## Controles implementados

### GitHub Actions y CI/CD

- Actions pinneadas por commit SHA en `ci.yml`, `security.yml` y `wiki-sync.yml`.
- Permisos minimos por workflow/job (`contents: read` por defecto; `security-events: write` solo para CodeQL; `contents: write` solo para wiki sync).
- `CodeQL` activo para Python con consultas `security-extended` y `security-and-quality`.
- Escaneo de secretos en CI con `detect-secrets` y baseline versionada.
- Escaneo de dependencias Python con `pip-audit` sobre `requirements.txt` raiz y de los casos.
- Modo gradual para dependencias: `soft` en PR, `hard` en `main`, `schedule` y `workflow_dispatch`.
- El caso 02 ya tiene suite propia y job dedicado en CI.

### Secretos y configuracion

- `.env.example` mas explicitos sobre DEMO vs LIVE y sobre no commitear credenciales reales.
- El portal ya no persiste valores implicitamente al copiar o descargar; solo guarda si pulsas `Guardar localmente`.
- El portal incorpora borrado explicito de almacenamiento local.
- Se documenta que `localStorage` guarda en texto claro y solo debe usarse en equipos confiables.
- Los casos con CORS configurable usan allowlists locales por defecto, no `*` abierto para navegadores externos.

### Exposicion externa opcional

- Los casos 01, 02, 09, 10 y 13 aceptan `DEMO_AUTH_TOKEN` para exigir el header `X-Demo-Token` en sus endpoints operativos.
- Los mismos casos aceptan `RATE_LIMIT_RPM` para aplicar rate limiting en memoria por cliente.
- `TRUST_PROXY_HEADERS=false` por defecto evita confiar en `X-Forwarded-For` salvo despliegue detras de un proxy controlado.
- Estos controles son opt-in para no romper la experiencia local ni los ejemplos pedagogicos.

### Agentes, tools y LLMs

- `hub.py` ya no usa `shell=True` para ejecutar `case.yml`.
- `hub.py` restringe ejecutables permitidos (`python`, `uvicorn`, `docker compose`) y bloquea metacaracteres de shell, `python -c` y rutas fuera del caso.
- Caso 13 endurecido como SQL read-only:
  - solo `SELECT/CTE`;
  - sin comentarios SQL ni objetos internos `sqlite_*`;
  - sin multiples sentencias;
  - limite maximo de filas;
  - conexion SQLite en modo solo lectura.
- Endpoints de casos operativos con validacion adicional de `thread_id`, `ticket_id`, `employee_id` o `question` para evitar abuso trivial o payloads descontrolados.
- Endpoints de salud dejan de exponer rutas locales innecesarias donde no aportaban valor operativo.

---

## Amenazas mitigadas

- ejecucion arbitraria sencilla desde `case.yml` o Hub CLI;
- filtrado accidental de secretos nuevos en archivos versionados;
- dependencia ciega de tags mutables en GitHub Actions;
- abuso basico de endpoints demo cuando se habilita el perfil de exposicion externa;
- exfiltracion de mayor volumen via SQL en el caso 13;
- sobreexposicion de CORS y de metadata interna en APIs de demo;
- persistencia accidental de secretos en el navegador solo por exportar `.env`.

---

## Amenazas fuera de alcance o parcialmente mitigadas

- prompt injection completa: el repo demuestra patrones de agentes, pero no implementa una sandbox universal contra instrucciones maliciosas en todo contenido posible;
- un mantenedor malicioso con permisos de merge puede cambiar codigo, workflows o `case.yml`;
- un equipo o navegador comprometido sigue pudiendo exfiltrar secretos locales;
- credenciales reales con privilegios excesivos siguen siendo riesgosas aunque el repo funcione en DEMO;
- el rate limiting actual es en memoria y best-effort; para Internet abierta sigue haciendo falta un reverse proxy o API gateway con controles duros.

---

## Recomendaciones operativas

- Usa secretos de menor privilegio posible y rotalos despues de demos externas.
- Prefiere rutas a archivos inyectados por runtime para credenciales JSON sensibles.
- Manten `ALLOWED_ORIGINS` acotado a los hosts realmente usados.
- Si necesitas exponer un caso fuera de localhost, activa `DEMO_AUTH_TOKEN`, `RATE_LIMIT_RPM`, TLS y un proxy seguro antes de abrirlo.
- Revisa los findings de `pip-audit` antes de promover cambios a `main`.

---

## Reporte de vulnerabilidades

Si detectas una vulnerabilidad en este repositorio:

1. Abre un Issue con la etiqueta `security` si el hallazgo es apto para disclosure publico.
2. Si el hallazgo expone credenciales, ejecucion remota o datos sensibles reales, evita publicarlo con detalle y coordina el reporte privado con el mantenedor.

---

## Limites de la documentacion

Este `SECURITY.md` describe la postura actual del repositorio, no una certificacion formal ni una garantia de seguridad total. La prioridad es seguridad realista y compatible con una experiencia de exploracion local de IA aplicada.
