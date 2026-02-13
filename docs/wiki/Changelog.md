# Changelog

Todas las novedades y cambios notables de este proyecto se documentarán en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [3.2.0] - 2026-02-13

### Añadido
- **Estándar Industrial (v3.2)**: Elevación del Caso 09 a estándares industriales con validación estricta y telemetría.
- **Validación con Pydantic**: Refactorización del estado del grafo de `TypedDict` a modelos de **Pydantic** para integridad de datos en runtime.
- **Telemetría (Trace IDs)**: Implementación de rastreo de solicitudes mediante `trace_id` único inyectado en logs JSON estructurados.
- **UI de Diagnóstico**: Visualización del Trace ID en el dashboard del Caso 09 para facilitar el debugging técnico.

## [3.1.0] - 2026-02-13

### Añadido
- **Modo AI vs Mock**: Implementación de `mock_api.py` para demos instantáneas sin LLM y `api.py` para ejecución real con LangGraph.
- **Resiliencia de Estado**: Integración de `SqliteSaver` en el Caso 09 para persistencia de hilos (`thread_id`).
- **Portal Local**: Script `serve_site.py` para levantar el portal principal en el puerto 8080 sin requerir Docker.
- **Dashboard Premium**: Interfaz premium para el Caso 09 con soporte de streaming NDJSON en tiempo real.

### Cambiado
- **Punto de Entrada Único**: Se consolidó el portal de `indexado.html` a `index.html` para simplificar el despliegue y la URL de acceso.
- **Estética Visual**: Actualización a la tipografía **Inter** y aplicación de efectos **Glassmorphism** en todo el portafolio.
- **Navegación Unificada**: Actualización masiva de links de retorno para asegurar la bidireccionalidad entre el portal y las demos.

### Corregido
- **Fallo de Conexión (Puerto 8009)**: Solución de conflictos de puerto mediante la opción de reutilización de dirección en servidores Python.
- **Broken Links**: Reparación de enlaces rotos en la Wiki y en el retorno del Caso 09.

## [3.0.0] - 2026-02-11
### Añadido
- Milestone de Observabilidad completado.
- Actualización global de todas las referencias de versión de v2.3.0 a v3.0.0.

## [2.3.0] - Anterior
### Añadido
- Implementación base de los 25 casos de uso (scaffolds).
- Dockerización inicial de la plataforma.
