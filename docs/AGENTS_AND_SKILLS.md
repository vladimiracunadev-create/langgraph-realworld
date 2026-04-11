# Infraestructura de Agentes y Skills

Este repositorio incluye una capa local de habilidades en `.agents/` para que asistentes automatizados puedan operar el repo con menos improvisacion y mas consistencia.

> [!IMPORTANT]
> El estandar tecnico del repositorio ya esta definido. Los agentes deben leer los skills correspondientes antes de ejecutar cualquier tarea, no redisenar lo que ya existe.

---

## Como funciona

1. El agente detecta una tarea compatible con un skill.
2. Lee el `SKILL.md` correspondiente — ahi esta el contrato completo.
3. Ejecuta el flujo del skill sin reanalizar decisiones ya tomadas.
4. Sincroniza codigo, documentacion, operacion y hardening cuando aplica.
5. Si algo no esta cubierto por el skill, lo senala explicitamente antes de improvisar.

---

## Skills disponibles

| Skill | Ruta | Cuando usarlo |
| :--- | :--- | :--- |
| **Crear Caso LangGraph** | `.agents/skills/crear_caso/SKILL.md` | Crear un caso nuevo o elevar un scaffold a OPERATIVO. Incluye contrato tecnico completo, estandar de interfaz web, DEMO/LIVE, Docker, tests y docs. |
| **Actualizar Documentacion** | `.agents/skills/actualizar_doc/SKILL.md` | Sincronizar README, docs/ y wiki local cuando cambia codigo o estado de un caso. |
| **Validar Caso LangGraph** | `.agents/skills/validar_caso/SKILL.md` | Auditar un caso existente: verificar Docker/CI, DEMO/LIVE, Hub, seguridad y docs. |

---

## Estandar de un caso completo

Un caso es completo cuando cumple el contrato definido en el skill `crear_caso`. Los puntos criticos son:

### Backend (obligatorio)

- `backend/src/graph.py` — StateGraph con TypedDict, nodos separados de integraciones
- `backend/src/api.py` — FastAPI con `/health`, `/ready`, `/api/run`, `/api/stream`
- `backend/src/settings.py` — deteccion de modo DEMO/LIVE por env vars
- `backend/src/integrations.py` — cliente real + fallback demo encapsulados
- `backend/tests/` — pruebas de flujo y API
- `backend/requirements.txt` — generado con pip-compile
- `backend/Dockerfile` + `backend/compose.yml`

### Interfaz web (obligatorio)

- `backend/web/index.html` — UI funcional en vanilla HTML/CSS/JS
  - Hero con descripcion en espanol del caso y su valor de negocio
  - Badge DEMO (naranja) / LIVE (verde) obtenido de `/health`
  - Enlace `← VOLVER AL HUB` a `http://localhost:8080/` (JetBrains Mono)
  - Formulario con datos de `data/` que cubran todas las opciones del select
  - Timeline de eventos en vivo via `/api/stream` (NDJSON)
  - Panel de resultados legible (badges, listas, scores)

### DEMO siempre funciona

- Sin tokens externos, el caso corre en DEMO con datos de `data/`
- Los archivos en `data/` tienen tantos registros como opciones tiene el select
- Los stubs en `integrations.py` producen resultados realistas y variados
- Ningun nodo del grafo falla si falta una API key — degrada a DEMO

### Navegacion bidireccional

- El hub (`index.html` raiz, puerto 8080) enlaza a `http://localhost:800X/web/`
- Cada interfaz de caso enlaza de vuelta al hub
- El caso aparece en `index.html` como OPERATIVO con el puerto correcto

---

## Principios que siguen los skills

- **Aislamiento por caso**: cada caso tiene puerto, backend, web, data, tests y compose propios.
- **Contratos explicitos**: TypedDict para estado, endpoints documentados, case.yml alineado.
- **DEMO/LIVE por configuracion**: el grafo funciona en ambos modos; solo cambian los helpers.
- **Documentacion alineada**: no documentar lo que el codigo aun no cumple.
- **Sin reanalisis de lo ya definido**: el skill es la fuente de verdad. Si esta en el skill, no se redisena.

---

## Orden de trabajo recomendado para agentes

Cuando se recibe la tarea de elevar un caso scaffold:

1. Leer el README del caso para entender el objetivo de negocio.
2. Leer `.agents/skills/crear_caso/SKILL.md` — es el contrato completo.
3. Proponer flujo LangGraph al usuario (nodos, estado, DEMO/LIVE, entrada/salida, UI).
4. Esperar aprobacion explicita antes de tocar codigo.
5. Implementar en orden: graph → integrations → api → web → tests → docs → compose.
6. Verificar que el select de la UI tenga datos reales en `data/` para todas las opciones.
7. Verificar navegacion: hub → caso → hub.
8. Actualizar CHANGELOG.md y, si aplica, ROADMAP.md.

Para el orden de prioridad de casos a elevar, consultar [`ROADMAP.md`](../ROADMAP.md).
