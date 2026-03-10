---
name: Actualizar Documentación
description: Sincronizar y actualizar toda la documentación del repositorio (Root, Docs, Wiki, Cases) a una nueva versión industrial.
---

# Skill: Actualizar Documentación Industrial

Este skill define el protocolo quirúrgico para actualizar la versión y el estado de madurez de **LangGraph Realworld** en todos sus puntos de contacto documentales.

## 🎯 Objetivo
Asegurar que el 100% de los archivos `.md`, `.html` y el CLI institucional (`hub.py`) reflejen la misma versión y taxonomía (Industrial vs Scaffold).

## 🛠️ Protocolo de Actuación

### 1. Auditoría de Versión (Audit Phase)
Antes de editar, localiza todas las referencias a la versión anterior para no dejar "huérfanos":
- `grep_search(query="v3.2.0")` (Ejemplo para buscar versiones viejas).
- `grep_search(query="Implementación Industrial")` para encontrar headers de sección.

### 2. Sincronización del Núcleo (Core Sync)
Actualiza los archivos en este orden de prioridad:
1.  **Portal Raíz**: `index.html` (Badges de las tarjetas).
2.  **README Principal**: `README.md` (Versión en las notas y tabla de estados).
3.  **Guías Técnicas**: `docs/ARCHITECTURE.md` y `docs/TECHNICAL_SPECS.md`.
4.  **Wiki Local**: `docs/wiki/Home.md` y `docs/wiki/README.md`.
5.  **Comunicación**: `RECRUITER.md`, `CHANGELOG.md` y `ROADMAP.md`.

### 3. Sincronización de Casos (Case Sync)
Para los casos marcados como **Industrial** (09, 10, 13):
- Actualizar el título en `cases/*/README.md`.
- Añadir/Actualizar el alert `> [!IMPORTANT]` con la versión exacta.

### 4. Actualización del CLI (Hub Sync)
- Editar `hub.py`.
- Localizar el diccionario o lógica de estados (`cmd_list`).
- Actualizar el string de retorno (ej. `"Industrial (v3.4.0)"`).

## ⚠️ Estrategia "Surgical Match" (Evitar Fallos de Edición)
Si un header contiene caracteres especiales (como emojis o símbolos de construcción) que causan fallos en `replace_file_content`:
1.  **Divide la búsqueda**: En lugar de buscar la línea completa, busca solo la parte de texto segura (ej: `Implementación Industrial (v3.2.0)`).
2.  **Usa Contexto**: Incluye la línea siguiente si es única para fijar el punto de edición.

## ✅ Lista de Verificación (Verification)
- [ ] ¿`grep` devuelve 0 resultados para la versión antigua?
- [ ] ¿Los badges en `index.html` coinciden con los READMEs de los casos?
- [ ] ¿El `hub.py list` muestra la versión correcta en la terminal?
- [ ] ¿El `CHANGELOG.md` tiene la fecha y versión actualizadas?

## 🚀 Despliegue Git
Ejecutar comandos individuales (PowerShell friendly):
1. `git add .`
2. `git commit -m "Industrial Documentation Sync (vX.X.X): Comprehensive audit and version alignment"`
3. `git push origin main`
