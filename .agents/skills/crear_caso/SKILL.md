---
name: Crear Caso LangGraph
description: Crear un nuevo caso de uso LangGraph desde cero y levantarlo, instalando dependencias, puertos aislados y reiniciando docker.
---

# Skill: Creación de Nuevo Caso LangGraph

Este skill automatiza y te guía en el proceso para crear un nuevo caso de LangGraph en el repositorio, de manera aislada y sin romper los casos anteriores, da indicaciones claras y precisas al usuario, siempre en español. 

Sigue estos pasos estrictamente cuando el usuario invoque el skill:

## Principios obligatorios

1. **No romper casos existentes.** Nunca modificar la lógica interna de casos ya resueltos, salvo que el usuario pida explícitamente una corrección puntual.
2. **Los Casos 09 y 10 son plantillas vivas.** Úsalos como referencia arquitectónica, no como texto de marketing.
3. **La evidencia manda.** Antes de afirmar que un caso está “completado”, “industrial” o “real-world”, verifica estructura, endpoints, streaming, Docker, tests y metadata del caso.
4. **Sincronización total.** No basta con crear el caso: hay que alinear `case.yml`, `docker-compose.yml`, `hub.py`, `index.html`, README y docs asociadas.
5. **Modo híbrido obligatorio.** Todo caso nuevo debe poder funcionar en modo demo local y quedar preparado para integraciones reales mediante variables de entorno.
6. **Aislamiento por caso.** Cada caso debe tener puerto, datos, backend, web, tests y compose propios.

## Paso 1: Analizar el Caso
1. Lee y analiza el caso solicitado por el usuario. 
2. Identifica el rol de los agentes, la arquitectura de LangGraph (lineal, router, loops, state_schema) y las herramientas (tools) o integraciones necesarias.
3. Identifica el siguiente número de caso disponible revisando la carpeta `cases/` (ej: si el último es `10-onboarding-empleados`, el nuevo o siguientes deberían ser `11-...`).

## Paso 2: Proponer Flujo y Esperar Aprobación (¡CRÍTICO!)
1. Crea un artefacto `implementation_plan.md` con el flujo detallado propuesto: nodos, dependencias y estructura de archivos a crear bajo la nueva carpeta del caso.
2. Usa la herramienta `notify_user` pasando el artefacto en `PathsToReview` y marcando `BlockedOnUser: true`. 
3. Pide explícitamente al usuario que apruebe el flujo propuesto. 
4. **Si el usuario rechaza**: Modifica el plan siguiendo sus indicaciones y vuelve a pedir aprobación. **NO SIGAS al Paso 3 hasta tener aprobación.**

## Paso 3: Crear el Código Genuino y Estructura Aislada
Una vez aprobado el plan, crea la estructura de directorios y archivos. Respeta el patrón de arquitectura ya existente en el proyecto:
- Crea las carpetas `cases/XX-nombre-del-caso/backend/src`, `web`, `data`, etc.
- Escribe el código en Python (`graph.py`, `api.py` FastAPI con `stream_mode="values"`, `settings.py`).
- Crea los archivos estáticos HTML/JS necesarios.
- Crea el `requirements.txt` específico de ese caso bajo `backend/`.
- No toques el código interno de las carpetas de los casos anteriores `01` a `XX-1`.

## Paso 4: Instalar y Verificar Dependencias
1. En la carpeta `backend` del nuevo caso, asegúrate de que exista un entorno virtual (o créalo si corresponde) y corre la instalación de dependencias `pip install -r requirements.txt`.
2. Verifica que las instalaciones hayan sido exitosas revisando los logs. Si faltan paquetes (ej. `uvicorn`, `fastapi`, `langgraph`), agrégalos e instálalos.

## Paso 5: Asignar un Puerto Localhost Propio
1. Busca un puerto que no esté en uso. Por convención en este proyecto, los puertos inician en 8000+XX. (Ej. el caso 10 usa 8010. El caso 11 usará `8011`).
2. Configura tu `api.py` / entorno para usar este puerto dedicado, asegurando aislamiento total durante el desarrollo.
3. Opcional: Si el repositorio tiene un archivo de gestión global como `docker-compose.yml` o `launch_all.py`, modifícalo para exponer y levantar también el contenedor/proceso de este nuevo puerto.

## Paso 6: Bajar y Subir los Servicios Docker
1. Detén los entornos existentes usando `docker compose down` (en la raíz o donde aplique, según estructurado).
2. Integra el nuevo servicio en `docker-compose.yml` (e.g., servicio `caseXX` en el puerto `80XX:80XX`).
3. Levanta los contenedores y reconstruye la imagen para incluir el nuevo componente: `docker compose up -d --build`.

## Paso 7: Revisión Manual del Usuario
Notifica al usuario mediante `notify_user` que el caso está levantado e infórmale el puerto exacto (e.g. `http://localhost:8011`). Indícale que puede revisar el caso funcionando, e indícale que estás a la espera para realizar correcciones sobre él.

## Paso 8: Actualizar el `index.html` principal

Siempre que un caso se cree o mejore:

- agregar o actualizar su enlace en la portada;
- mostrar nombre y descripción breve;
- verificar que la ruta funcione;
- evitar enlaces rotos o error 404;
- mantener el estilo visual existente.

## Paso 9: Verificar consistencia final

Antes de cerrar:

- confirmar que el caso quedó visible;
- confirmar que el `index.html` principal quedó actualizado;
- confirmar que la documentación coincide con el estado real;
- confirmar que no se tocaron los Casos 09 y 10;
- confirmar que no se rompió el repositorio.

## Resultado esperado

Este skill debe dejar:

- un caso creado o mejorado;
- los Casos 09 y 10 intactos;
- la documentación actualizada;
- el `index.html` principal actualizado;
- el caso visible desde la portada;
- el repositorio consistente y sin roturas;
- debes levantar tambien si vas a subir el `index.html`, el localhost:8080;
-revisa si el 8080 si esta en uso, bajalo o mejor limpia todo el docker activo (imagenes,volumenes,contenedores) y que el 8080, funcione con este repositorio exclusivamente.
- recuerda el sistema debe funcionar en modo demo local y quedar preparado para integraciones reales mediante variables de entorno.
