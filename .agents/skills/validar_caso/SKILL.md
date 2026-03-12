---
name: Validar Caso LangGraph
description: Validar y endurecer un caso de uso LangGraph dentro de este monorepo. Usar cuando el usuario pida revisar un caso, verificar que un caso nuevo o existente quedó realmente operativo, diagnosticar fallas de Docker o CI, comprobar consistencia entre backend, case.yml, Hub, portal, tests y documentación, o antes de declarar un caso como operativo o industrial.
---

# Skill: Validar Caso LangGraph

Usar este skill para auditar casos LangGraph ya existentes en el repositorio. Escribir siempre en español. Priorizar evidencia y detectar regresiones antes de declarar que un caso quedó listo.

## Objetivo

Confirmar que un caso:

- compila y arranca con el contrato real del repo;
- tiene coherencia entre código, Docker, Hub y docs;
- no depende de supuestos falsos sobre contexto de build, rutas o variables;
- degrada correctamente a DEMO cuando faltan integraciones reales.

## Cuándo usarlo

Activar este skill cuando ocurra cualquiera de estos escenarios:

- el usuario pide "revisar", "validar", "auditar" o "endurecer" un caso;
- un caso nuevo fue implementado y hay que confirmar si quedó operativo;
- CI falla en `docker build`, `pytest`, imports o rutas;
- hay dudas sobre `DEMO/LIVE`, `case.yml`, `hub.py`, `compose` o `index.html`;
- antes de actualizar README o docs para marcar un caso como listo.

## Principios obligatorios

1. La validación manda sobre la intención. Si algo falla, reportarlo aunque la implementación parezca correcta.
2. No asumir que el contexto de Docker local es el mismo que el de CI; comprobar ambos cuando aplique.
3. No declarar un caso “operativo” o “industrial” sin evidencia concreta.
4. No corregir documentación primero; validar implementación y operación antes.
5. Si aparece un artefacto temporal o dependencias locales ad hoc, excluirlos del resultado final salvo que el usuario pida conservarlos.

## Contrato mínimo a validar

Revisar, como mínimo:

- `backend/src/graph.py`
- `backend/src/api.py`
- `backend/src/settings.py`
- `backend/Dockerfile`
- `backend/compose.yml`
- `case.yml`
- `backend/tests/`
- `backend/web/`
- integración en `hub.py` si el caso usa `case.yml`
- integración en `index.html` y docs si el caso fue promovido

## Checklist de validación

### 1. Estructura

- confirmar que existen archivos base del caso;
- confirmar que los imports del backend son coherentes;
- confirmar que `case.yml` apunta a comandos y rutas reales.

### 2. API y grafo

- verificar que LangGraph vive realmente en `graph.py`;
- verificar que `api.py` no concentra indebidamente toda la lógica;
- verificar endpoints mínimos: `/health`, `/ready` y endpoint principal;
- verificar streaming si el caso lo promete.

### 3. DEMO y LIVE

- comprobar que falta de `OPENAI_API_KEY` no rompe el caso;
- comprobar que el fallback DEMO es explícito y observable;
- comprobar que LIVE solo se activa con configuración válida;
- comprobar que docs y UI describen el mismo comportamiento.

### 4. Docker y CI

- validar el `Dockerfile` con el contexto real que usa CI;
- validar que no existan `COPY` fuera de contexto;
- validar coherencia entre `Dockerfile`, `compose.yml` y `docker-compose.yml`;
- validar si los volúmenes compensan datos no empaquetados en la imagen.

### 5. Hub y portal

- validar `python hub.py list`;
- validar que el estado mostrado coincida con la realidad técnica;
- validar que la portada enlace al destino correcto;
- validar que no se haya promovido un caso solo documentalmente.

### 6. Documentación

- README del caso;
- README raíz si aplica;
- `docs/INSTALL.md`, `docs/REQUIREMENTS.md`, `docs/ARCHITECTURE.md`, `docs/TECHNICAL_SPECS.md`;
- wiki local si el repositorio la mantiene sincronizada.

## Flujo de trabajo

### Paso 1: Recolectar evidencia

Leer:

- README del caso;
- archivos backend clave;
- compose y Dockerfile;
- `case.yml`;
- referencias en `hub.py`, `README.md`, `index.html` y docs.

### Paso 2: Validar localmente

Intentar, cuando el entorno lo permita:

- `python -m compileall`
- imports directos del backend
- `python -m pytest`
- `docker build`
- `python hub.py list`

Si algo no puede ejecutarse por sandbox, permisos o dependencias, decirlo explícitamente.

### Paso 3: Diagnosticar brechas

Clasificar hallazgos en estas categorías:

- estructura;
- ejecución Python;
- Docker/CI;
- DEMO/LIVE;
- documentación;
- integración monorepo.

### Paso 4: Corregir

Aplicar el fix mínimo que elimine la causa real, no solo el síntoma visible.

### Paso 5: Revalidar

Volver a correr exactamente la comprobación que falló.

## Resultado esperado

Este skill debe dejar:

- un diagnóstico claro del estado real del caso;
- fixes concretos para operación, Docker o docs si hacían falta;
- evidencia de qué se pudo validar y qué no;
- un caso listo para ser marcado como operativo o una lista concreta de brechas restantes.
