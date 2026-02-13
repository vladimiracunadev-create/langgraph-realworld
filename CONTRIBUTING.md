# Guía de Contribución (CONTRIBUTING)

> [!NOTE]
> **Versión**: 1.1.0 | **Estado**: Activo | **Audiencia**: Colaboradores, Desarrolladores Open Source

Bienvenido al ecosistema de **LangGraph Realwork**. Este es un repositorio diseñado bajo una arquitectura de **Monorepo Modular** (25 casos de uso). Para mantener la excelencia técnica y la portabilidad, seguimos reglas estrictas de contribución.

---

## 🏗️ Estructura de Contribución

Cada caso de uso debe ser **autocontenido** y seguir el patrón de "Agente con Estado".

- **Ubicación**: Todo nuevo caso o mejora debe vivir en `cases/NN-slug/`.
- **Estructura Requerida**:
  - `backend/Dockerfile`: Para garantizar la residencia y repetibilidad.
  - `backend/requirements.txt`: Gestión de dependencias aislada.
  - `backend/src/`: Código fuente siguiendo patrones 12-factor.
  - `demo/index.html`: Una interfaz de demostración funcional (preferiblemente con Glassmorphism).

---

## 🛠️ Estándares de Código

Para asegurar la calidad, el pipeline de CI rechazará cualquier cambio que no cumpla con:

1.  **Python**:
    - Linter & Formatter: **Ruff**. Ejecuta `ruff check .` antes de subir.
    - Estilo: Adhesión estricta a tipos mediante `typing` y `Annotated`.
2.  **Documentación**:
    - Cada caso debe tener su propio `README.md` explicando el flujo del grafo.
    - Los diagramas Mermaid son obligatorios para visualizar el `StateGraph`.

---

## 🚀 Flujo de Trabajo (Workflow)

1.  **Fork & Branch**: Crea una rama descriptiva (ej: `feature/case-26-legal-advisor`).
2.  **Docker First**: Asegúrate de que tu caso corra perfectamente con `docker build`.
3.  **Smoke Tests**: Agrega un archivo `compose.smoke.yml` si el caso está "Implementado".
4.  **Pull Request**: Describe el valor de negocio y el patrón de LangGraph utilizado.

---

## 🛡️ Seguridad

Nunca incluyas secretos. El pre-commit hook de `detect-secrets` bloqueará cualquier intento de subir claves de APIs. Si encuentras una vulnerabilidad, consulta nuestro [SECURITY.md](SECURITY.md).

---
> [!IMPORTANT]
> **Buscamos Calidad sobre Cantidad.** Preferimos casos con grafos bien definidos, manejo de errores robusto y dashboards pulidos.
