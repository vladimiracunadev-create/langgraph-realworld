# 🛠️ Especificaciones Técnicas

> [!NOTE]
> **Versión**: 3.4.0 | **Estado**: Industrial | **Audiencia**: Seniors, DevOps

Este documento detalla el stack tecnológico, los estándares de código y los contratos de observabilidad para asegurar la excelencia operativa del proyecto.

---

## 🛠️ Stack Tecnológico

### Backend & AI

- **Python 3.11+**: Lenguaje base para la lógica de agentes y API.
- **LangGraph**: Framework de orquestación para grafos cíclicos con estado.
- **FastAPI**: Servidor ASGI para la exposición de endpoints y streaming NDJSON.
- **Tenacity**: Librería para la implementación de políticas de reintento avanzadas.
- **SQLite**: Motor persistente para el almacenamiento de checkpoints del grafo.

### Frontend & Demo

- **Vanilla JavaScript (ES6+)**: Consumo de streams SSE/NDJSON y renderizado dinámico.
- **Tailwind CSS / Glassmorphism**: Estilizado moderno para dashboards de alta fidelidad.
- **Chart.js**: Visualización de datos dinámica y dashboards de BI.
- **Mermaid.js**: Visualización dinámica de la arquitectura del grafo en tiempo de ejecución.

---

## 🏗️ Principios Arquitectónicos

1.  **Aislamiento por Caso (Modularidad)**: Cada carpeta en `cases/` es un ecosistema independiente para evitar regresiones cruzadas.
2.  **Estado Externo (Idempotencia)**: El estado del agente se persiste en cada paso, permitiendo la recuperación ante reinicios.
3.  **Configuración via Entorno**: Adhesión estricta a *12-Factor App* usando archivos `.env` y variables de entorno del sistema.

---

## 🏥 Contrato de Salud y Resiliencia (Observability Standard)

Siguiendo nuestro estándar de observabilidad, cada backend debe implementar:

### 1. Endpoint de Liveness (`/health`)
- **Propósito**: Verificar que el proceso Python/FastAPI esté activo.
- **Respuesta**: 200 OK - `{"status": "ok", "ts": <timestamp>}`.

### 2. Endpoint de Readiness (`/ready`)
- **Propósito**: Confirmar que el grafo de LangGraph ha compilado correctamente y está listo para recibir transacciones.
- **Respuesta**: 200 OK - `{"status": "ready"}` o 503 si falla la compilación.

### 3. Registro de Eventos (Structured Logging)
- **Formato**: JSON.
- **Campos Obligatorios**: `ts`, `level`, `name`, `msg`, `trace_id` (si está disponible).
- **Destino**: `stdout` (para captura por Docker/K8s).

---

## 🔒 Seguridad e Integridad

- **Secret Scanning**: Uso de `detect-secrets` y `TruffleHog` en la fase de CI.
- **Non-Root Images**: Todas las imágenes de Docker corren con un UID no privilegiado (1000).
- **SAST**: Análisis estático constante mediante el pipeline de GitHub Actions.

---

## 🛡️ Contrato de Resiliencia (Resilience Standards)

Para garantizar la robustez, cada agente debe cumplir con:

1.  **Reintentos**: Mínimo 3 intentos para llamadas de red.
2.  **Persistencia**: Uso obligatorio de un `checkpointer` (SQLite/Redis) para threads de larga duración.
3.  **Timeout**: Límite máximo de 60 segundos por paso del grafo (evita bucles infinitos y costos excesivos).
4.  **Error Schema**: Todas las excepciones deben ser capturadas y transformadas en eventos de log estructurados antes de propagarse.

---

## 🛠️ Guía de Estilo

- **Ruff**: Linter y formateador oficial. Se debe ejecutar antes de cada commit.
- **CamelCase**: Para nombres de clases y componentes React/Frontend.
- **snake_case**: Para variables, funciones y métodos en Python.
- **Kebab-case**: Para nombres de carpetas y archivos estáticos.
---

## 🧭 Navegación
- [⬅️ Volver al README](../README.md)
- [🏗️ Arquitectura](ARCHITECTURE.md)
- [🚀 Instalación](INSTALL.md)
- [🛡️ Seguridad](../SECURITY.md)
