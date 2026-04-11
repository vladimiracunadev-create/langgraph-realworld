---
name: Crear Caso LangGraph
description: Crear o elevar un caso de uso LangGraph dentro de este repositorio siguiendo el estandar industrial local. Usar cuando el usuario pida crear un caso nuevo, convertir un scaffold en un caso real, agregar backend FastAPI con LangGraph, preparar modo DEMO/LIVE, integrar Docker, tests, portal y documentacion, o cuando haya que mejorar un caso existente sin romper los demas.
---

# Skill: Crear Caso LangGraph

Usar este skill para crear o mejorar casos LangGraph en este monorepo. Escribir siempre en espanol. Priorizar evidencia, aislamiento por caso y compatibilidad con el estandar del repo.

## Principios obligatorios

1. No romper casos existentes. No modificar la logica interna de otros casos salvo que el usuario lo pida.
2. Usar los casos 09, 10 y 13 como referencia tecnica viva. Tomar patrones de arquitectura, no marketing.
3. La evidencia manda. No declarar un caso como completo o industrial sin verificar estructura, endpoints, streaming, Docker, tests y documentacion.
4. Sincronizacion total. Si el caso cambia, alinear `case.yml`, `docker-compose.yml`, `hub.py`, `index.html`, README y docs relacionadas cuando corresponda.
5. Modo hibrido obligatorio. Todo caso debe funcionar en DEMO sin dependencias externas y mejorar a LIVE cuando exista configuracion real utilizable.
6. Aislamiento por caso. Cada caso debe tener puerto, backend, web, data, tests y compose propios.
7. LangGraph vive en el backend Python. La UI solo consume la API; no presentar HTML o Docker como si fueran LangGraph.
8. Hacer supuestos razonables y avanzar. Preguntar solo cuando una decision tenga impacto no obvio o riesgo real.

## Contrato tecnico minimo de un caso real

Un caso real en este repo debe incluir, como minimo:

- `backend/src/graph.py` con un `StateGraph` o equivalente de LangGraph
- `backend/src/api.py` con FastAPI
- `backend/src/settings.py`
- `backend/src/integrations.py` si hay tools, LLM o adaptadores externos
- `backend/web/index.html` o UI equivalente
- `backend/tests/` con pruebas de flujo y API
- `backend/requirements.txt`
- `backend/Dockerfile`
- `backend/compose.yml`
- `case.yml` si el caso se integra al Hub
- `GET /health`
- `GET /ready`
- endpoint de ejecucion, por ejemplo `POST /api/run`
- endpoint de streaming cuando la UX lo amerite, preferentemente `GET /api/stream` con `stream_mode="values"`

## Contrato DEMO y LIVE

Siempre implementar este comportamiento:

- Si no existe configuracion usable para LLM o integraciones reales, el caso corre en `DEMO`.
- Si existe configuracion minima valida para LLM o integraciones reales, el caso corre en `LIVE`.
- El grafo debe seguir funcionando en ambos modos; solo cambian algunos nodos o helpers.
- Exponer el modo actual en respuestas de API o metadata visible para la UI.
- Nunca fallar todo el caso solo porque falta una API key; degradar a DEMO.

Regla recomendada:

- `settings.py` detecta si hay credenciales y flags validos.
- `integrations.py` encapsula cliente real y fallback demo.
- `graph.py` consume helpers agnosticos al modo.
- `api.py` informa `mode=DEMO|LIVE`.

## Estandar de la interfaz web

La interfaz `backend/web/index.html` es OBLIGATORIA en todo caso. No es un JSON demo ni un enlace estatico. Es una UI funcional que opera en tiempo real contra el backend del caso.

### Que debe incluir siempre

- **Hero con descripcion en texto**: explicar en espanol que hace el caso, por que existe y que problema de negocio resuelve. El usuario debe entenderlo sin leer codigo.
- **Indicador de modo**: badge visible de DEMO (naranja) o LIVE (verde), obtenido de `GET /health`.
- **Enlace de retorno**: `← VOLVER AL HUB` apuntando a `http://localhost:8080/` con font JetBrains Mono (patron existente en todos los casos del repo).
- **Formulario de entrada**: select, inputs o botones que permitan ejecutar el caso con datos de prueba reales del directorio `data/`.
- **Timeline de eventos en vivo**: consumir `GET /api/stream` via NDJSON y mostrar cada evento a medida que llega.
- **Panel de resultados**: mostrar el estado final del grafo de forma legible (badges, tablas, listas).
- **Pillrow de tecnologias**: pills con las tecnologias clave del caso (LangGraph, nodos usados, modo, puerto).

### Estandar visual

- Vanilla HTML/CSS/JS sin frameworks.
- Tema oscuro coherente con el resto del repo (fondo `#07111f` o similar, acentos de color propios del caso).
- Responsive, sin scroll horizontal en desktop ni mobile.
- Fuentes: Inter para texto, JetBrains Mono para codigo, monoespaciado y pills tecnicas.

### Estandar de datos DEMO

- El directorio `data/` debe contener registros reales suficientes para cubrir todas las opciones del select o formulario de la UI.
- Si el select tiene 3 opciones, el archivo JSON de datos debe tener 3 registros con IDs que coincidan exactamente.
- DEMO no significa "devolver siempre el mismo dato". Significa "funcionar sin tokens externos con datos de muestra reales".
- Los stubs en `integrations.py` deben producir resultados variados y realistas que demuestren el flujo del grafo.

### Lo que NO es un caso

- Un caso NO es un enlace a un JSON estatico.
- Un caso NO es una pagina HTML con un boton que llama a una URL hardcodeada.
- Un caso NO es "funciona si tienes el token". El DEMO debe funcionar siempre, sin excepciones.
- Un caso NO esta terminado si la UI no existe o si los datos de demo no cubren todas las opciones disponibles.

## Flujo de trabajo

### Paso 1: Entender el caso

1. Leer el README del caso objetivo y revisar si ya existe scaffold, demo o backend parcial.
2. Identificar objetivo de negocio, actores, entrada, salida y valor de la automatizacion.
3. Definir donde aporta LangGraph: estado, nodos, routers, loops, tools, checkpoints, streaming.
4. Revisar referencias en casos 09, 10 y 13 para copiar solo patrones utiles.

### Paso 2: Proponer el flujo antes de implementar

Antes de tocar codigo, crear `implementation_plan.md` en la raiz del repo o en la carpeta del caso con:

- objetivo del caso
- flujo LangGraph propuesto
- estado tipado sugerido
- nodos y routers
- archivos a crear o modificar
- puertos y endpoints
- modo DEMO/LIVE
- plan de verificacion

Luego resumir ese plan al usuario y pedir aprobacion explicita. No avanzar a implementacion hasta tener esa aprobacion.

Si el usuario ya aprobo el enfoque en la conversacion, continuar sin volver a pedir permiso.

### Paso 3: Implementar la estructura aislada del caso

Respetar esta estructura cuando aplique:

- `cases/XX-slug/README.md`
- `cases/XX-slug/case.yml`
- `cases/XX-slug/data/`
- `cases/XX-slug/backend/.env.example`
- `cases/XX-slug/backend/requirements.txt`
- `cases/XX-slug/backend/Dockerfile`
- `cases/XX-slug/backend/compose.yml`
- `cases/XX-slug/backend/compose.smoke.yml`
- `cases/XX-slug/backend/src/__init__.py`
- `cases/XX-slug/backend/src/settings.py`
- `cases/XX-slug/backend/src/integrations.py`
- `cases/XX-slug/backend/src/graph.py`
- `cases/XX-slug/backend/src/api.py`
- `cases/XX-slug/backend/tests/`
- `cases/XX-slug/backend/web/index.html`

No crear archivos innecesarios. Mantener el caso autocontenido.

### Paso 4: Implementar LangGraph de forma explicita

El grafo debe quedar claramente visible en `graph.py`.

Buenas practicas esperadas:

- usar `TypedDict` o esquema equivalente para el estado
- separar nodos puros de integraciones externas
- usar eventos o snapshots si la UI necesita trazabilidad
- usar checkpointer apropiado al nivel del caso, por ejemplo `MemorySaver` si favorece portabilidad
- si existe streaming, usar `graph.stream(..., stream_mode="values")` o equivalente adecuado

Evitar:

- esconder toda la logica del caso dentro de `api.py`
- mezclar UI con el grafo
- acoplar el caso a una LLM obligatoria

### Paso 5: Puerto y ejecucion

Convencion del repo:

- usar `8000 + case_id` para el backend del caso
- mantener `8080` para el portal raiz cuando se use el sitio principal

Actualizar compose raiz o herramientas globales solo si realmente integran el caso. No tocar mas de lo necesario.

### Paso 6: Docker y entorno local

Preparar dos caminos de ejecucion cuando sea razonable:

- compose aislado del caso
- ejecucion local directa del backend

No limpiar imagenes, volumenes o contenedores de forma destructiva salvo pedido expreso del usuario.
No bajar servicios ajenos innecesariamente. Verificar primero antes de intervenir puertos.

### Paso 7: Verificacion real

Antes de cerrar, comprobar en la medida de lo posible:

- imports y compilacion Python
- tests del caso
- health y ready
- endpoint principal de ejecucion
- streaming si aplica
- rutas de web
- consistencia de `case.yml`
- visibilidad del caso en `hub.py` y en el portal si fue integrado

Si algo no pudo verificarse, decirlo explicitamente.

### Paso 8: Sincronizacion de documentacion

Actualizar solo la documentacion afectada por el cambio real:

- README del caso
- `README.md` raiz si cambia el estado general del portfolio
- `docs/INSTALL.md` si cambia la forma de ejecutar
- `docs/ARCHITECTURE.md` o `docs/TECHNICAL_SPECS.md` si el caso altera el estandar observable
- `index.html` si el caso debe quedar visible desde la portada

No prometer en docs algo que el codigo aun no cumple.

## Criterios para declarar un caso listo

Decir que un caso quedo resuelto solo si existe evidencia de:

- LangGraph implementado en backend
- API funcional
- modo DEMO operativo
- fallback correcto cuando no hay LLM
- LIVE preparado cuando hay configuracion real
- arranque reproducible
- documentacion alineada
- validacion minima ejecutada o limitaciones explicadas

## Resultado esperado

Este skill debe dejar:

- un caso nuevo o mejorado
- un flujo LangGraph claro y visible en backend
- modo DEMO automatico y modo LIVE cuando exista LLM utilizable
- integracion razonable con compose, hub y portal si corresponde
- documentacion consistente con el estado real
- el repositorio sin roturas innecesarias
