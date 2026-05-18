# Arquitectura del Sistema

> [!NOTE]
> **Version**: 4.11.0 | **Estado**: Industrial | **Audiencia**: Arquitectos Cloud, System Designers, DevOps

## Vision General

**LangGraph Realworld** usa un patron de monorepo con microservicios encapsulados por caso. Cada caso operativo implementado reside en su propio subdirectorio con backend FastAPI, UI ligera, configuracion local y `case.yml` para orquestacion reproducible.

## Capas Principales

- **Portal raiz**: `index.html` como punto de entrada, navegacion y ayuda para configuracion opcional de APIs.
- **Backends operativos**: casos 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 17, 18, 19, 21, 22 y 25 con endpoints reales, modo DEMO/LIVE y contratos de estado.
- **Orquestacion agentica**: LangGraph con `TypedDict`, edges condicionales, checkpoints y herramientas acotadas por dominio.
- **Operacion local**: Docker Compose, Hub CLI y arranque directo por `uvicorn`.
- **Seguridad automatizada**: GitHub Actions con pinning, CodeQL, `detect-secrets`, `pip-audit` y validacion dedicada de los 21 casos operativos.

## Modelo de seguridad integrado

La arquitectura es local-first y pedagogica, pero ya incorpora limites operativos reales:

- CORS con allowlists donde hay consumo cross-origin.
- `hub.py` sin `shell=True` y con allowlist de comandos.
- Validacion de inputs en endpoints operativos.
- SQL read-only y sanitizacion adicional en el caso 13.
- Perfil opcional de exposicion externa con `DEMO_AUTH_TOKEN`, `RATE_LIMIT_RPM` y `TRUST_PROXY_HEADERS`.

## Dual Mode

Los casos operativos no dependen de una API real para ser explorados:

1. Si faltan credenciales, caen a DEMO de forma explicita.
2. Si hay configuracion valida, pueden activar integraciones reales por caso.
3. La documentacion y el portal distinguen claramente entre demo, pruebas locales y uso con secretos reales.

## Implicancia practica

El repositorio no intenta ser una plataforma multi-tenant lista para Internet abierta. La arquitectura prioriza tres cosas a la vez:

- exploracion local sin friccion;
- ejemplos de agentes y automatizacion con valor real;
- hardening suficiente para no normalizar malas practicas de CI/CD, secretos o ejecucion.
