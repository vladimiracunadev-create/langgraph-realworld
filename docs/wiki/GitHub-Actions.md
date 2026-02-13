# Referencia de GitHub Actions (Wiki Async) 🚀

Este documento detalla los flujos de trabajo automatizados que mantienen la integridad, seguridad y sincronización del repositorio **LangGraph Realworld**.

---

## 🛰️ Visión General de CI/CD

El repositorio utiliza GitHub Actions para automatizar el ciclo de vida de desarrollo, desde el linting hasta el despliegue de la documentación.

### 1. Integración Continua (`ci.yml`)
- **Filtros**: Se activa en cada `push` o `pull_request` a la rama `main`.
- **Tareas**:
  - **Calidad de Python**: Ejecuta `ruff` y chequeos de sintaxis en el Caso 09.
  - **Build de Contenedores**: Valida que las imágenes de Docker de los 25 casos compilen correctamente mediante una matriz de estrategia.
  - **Smoke Tests**: Ejecuta pruebas de integración en entornos aislados.

### 2. Seguridad Automática (`security.yml`)
- **Filtros**: Ejecución semanal y tras cambios en archivos críticos.
- **Tareas**:
  - **Trivy**: Escaneo de vulnerabilidades en las imágenes de Docker.
  - **Secret Scanning**: Verificación de credenciales expuestas.

---

## 🔄 Wiki Async (Wiki Sync)

El componente **Wiki Async** es el encargado de mantener la documentación del repositorio sincronizada asíncronamente con la Wiki de GitHub.

### Funcionamiento (`wiki-sync.yml`)
- **Trigger**: Se activa automáticamente cuando se detectan cambios en la carpeta `docs/wiki/` de la rama `main`.
- **Acción**: Utiliza `Andrew-Chen-Wang/github-wiki-action` para empujar los cambios locales a la wiki externa del repositorio.
- **Beneficio**: Permite gestionar la documentación técnica como código (Docs-as-Code), manteniendo un historial de versiones claro.

### Estado de Sincronización
> [!NOTE]
> Cada página de la wiki incluye un comentario oculto `<!-- Sync: YYYY-MM-DD -->` que indica la última vez que el motor **Wiki Async** actualizó el contenido.

---

## 🛠️ Mantenimiento de Workflows

Para modificar estos flujos, edite los archivos YAML en la carpeta `.github/workflows/`. Asegúrese de probar los cambios en una rama separada antes de fusionarlos a `main` para evitar interrupciones en el "Wiki Async".
