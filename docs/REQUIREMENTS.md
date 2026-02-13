# Requisitos del Sistema (REQUIREMENTS)

Este documento define las especificaciones técnicas necesarias para ejecutar los casos de uso de **LangGraph Realworld** de manera óptima.

---

## 🖥️ Hardware

### Mínimo (Entorno de Pruebas)

- **CPU**: 2 Cores (2.0 GHz+) - Necesario para procesamiento paralelo de agentes.
- **RAM**: 4 GB (Docker Desktop / WSL2).
- **Almacenamiento**: 500 MB libres para imágenes Docker y persistencia de checkpoints.
- **Pantalla**: Resolución 1280x720 para visualización de dashboards.

### Recomendado (Producción / Escalado)

- **CPU**: 4 Cores+ (para múltiples hilos de LangGraph).
- **RAM**: 8 GB+.
- **Almacenamiento**: 2 GB+ (para logs históricos y bases de datos SQLite persistentes).
- **Red**: Acceso estable a internet para llamadas a APIs de LLM (OpenAI, Anthropic).

---

## 💾 Software

### Sistema Operativo

- **Windows**: 10/11 con WSL2 (Recomendado).
- **Linux**: Ubuntu 22.04 LTS (Optimizado para despliegues de CI/CD).
- **macOS**: Ventura+ (Apple Silicon preferido para local LLM testing).

### Stack de Desarrollo

- **Python**: Versión **3.11** o superior.
- **Docker**: Engine 24.0+ y Docker Compose 2.0+ (para `compose.smoke.yml`).
- **Make**: GNU Make 4.0+ (para uso de comandos rápidos).
- **Git**: 2.34+ (para gestión de monorepo).

---

## 🌐 Compatibilidad de Navegadores

Los dashboards de los casos (como el Caso 09) utilizan CSS moderno y Web APIs para streaming:

| Navegador | Versión Mínima | Estado |
| :--- | :--- | :--- |
| **Google Chrome** | 98+ | ✅ Optimizado |
| **Mozilla Firefox** | 95+ | ✅ Soportado |
| **Safari** | 15+ | ✅ Soportado |
| Internet Explorer | - | ❌ No Soportado |

---

## 📡 Matriz de Entorno

| Característica | Local (conda/venv) | Docker | Kubernetes (K8s) |
| :--- | :---: | :---: | :---: |
| Streaming SSE | ✅ | ✅ | ✅ |
| Persistencia SQLite | ✅ | ✅ (Volume) | ✅ (PVC) |
| Hub CLI | ✅ | ⚠️ (Limitado) | ❌ |
| Smoke Tests | ✅ | ✅ | ⚠️ (In-cluster) |

> **Nota**: Para el uso de LLMs reales, se requiere una clave de API válida (OpenAI, etc.) configurada en el archivo `.env`.
