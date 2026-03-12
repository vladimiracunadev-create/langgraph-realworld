# Changelog

Todas las novedades y cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado del repositorio continúa alineado con [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Documentación
- Sincronización de README, docs, wiki local y READMEs de casos para reflejar el estado real de los casos 09, 10 y 13.
- Corrección de claims antiguos sobre `Pydantic` y `SqliteSaver` como si aplicaran uniformemente a toda la tríada industrial.
- Estandarización de la narrativa operativa del caso 13 en Docker, Hub y modo local.

### Caso 13
- Endpoints `/health`, `/ready` y `/examples` documentados y operativos.
- Base demo regenerable con esquema consistente entre `sales`, `customers` y `products`.
- Tests mínimos para helpers SQL y seeding de datos.

## [3.4.0] - 2026-03-10

### Añadido
- Dashboard BI inicial para el caso 13.
- Tríada industrial consolidada alrededor de los casos 09, 10 y 13.
- Reestructuración del portal y actualización visual del portafolio.

## [3.2.0] - 2026-02-13

### Añadido
- Endurecimiento operativo del caso 09.
- Telemetría con `trace_id` en la capa API del caso 09.
- Primer salto fuerte de documentación técnica y narrativa industrial.

## [3.1.0] - 2026-02-13

### Añadido
- Portal local con `serve_site.py`.
- Demos premium y primeros flujos NDJSON en tiempo real.

## [3.0.0] - 2026-02-11

### Añadido
- Primer milestone de observabilidad.
- Actualización global de referencias de versión de la línea 2.x a 3.0.

## [2.3.0] - Anterior

### Añadido
- Base inicial de los 25 casos.
- Dockerización temprana de la plataforma.