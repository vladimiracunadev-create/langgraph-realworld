# 📋 Requisitos del Sistema

> [!NOTE]
> **Versión**: 3.4.0 | **Estado**: Estable | **Audiencia**: Infraestructura, DevOps, Reclutadores

Este documento define las especificaciones técnicas necesarias para ejecutar los casos de uso de **LangGraph Realworld** de manera óptima.

---

## 🖥️ Hardware

### Mínimo (Entorno de Pruebas)
- **CPU**: 2 Cores (2.0 GHz+) - Necesario para procesamiento paralelo básico.
- **RAM**: 4 GB (Docker / WSL2).
- **Almacenamiento**: 1 GB libre para imágenes y persistencia básica.

### Recomendado (Desarrollo Activo / Producción)
- **CPU**: 4 Cores+ (optimizado para múltiples hilos de LangGraph).
- **RAM**: 8 GB - 16 GB (para levantar la **Tríada Industrial** simultáneamente).
- **Almacenamiento**: 5 GB+ (para logs históricos, bases de datos SQLite y volúmenes Docker).

### Escala / Extreme (Cargas de Producción)
- **CPU**: 8 Cores+ (Instancias tipo c6g.2xlarge en AWS).
- **RAM**: 32 GB (para manejo de contexto extenso y grafos de alta concurrencia).
- **Red**: Acceso estable con latencia < 150ms a proveedores de LLM.

---

## 📡 Requisitos de Red y Conectividad

- **Ancho de Banda**: Mínimo 2 Mbps de subida/bajada para streaming fluido de eventos.
- **Puertos**: Debe tener libre el rango `8009`, `8010` y `8013` para la Tríada Industrial, y `8080` para el portal.
- **Protocolos**: Soporte para HTTP/1.1 (Chunked Transfer Encoding) para streaming de NDJSON.

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

---

## 🧭 Navegación
- [⬅️ Volver al README](../README.md)
- [🚀 Instalación](INSTALL.md)
- [🏗️ Arquitectura](ARCHITECTURE.md)
- [🛠️ Especificaciones Técnicas](TECHNICAL_SPECS.md)
