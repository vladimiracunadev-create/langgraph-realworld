# 🤖 Infraestructura de Agentes y Skills

Este repositorio utiliza una carpeta especializada `.agents/` para orquestar la colaboración entre el usuario y los asistentes de IA (como Antigravity). Esta carpeta contiene la "inteligencia operativa" que permite automatizar tareas complejas manteniendo la consistencia industrial del proyecto.

---

## 📂 Estructura de `.agents/`

La carpeta se divide en dos componentes principales:

1.  **`skills/`**: Directorios que contienen un archivo `SKILL.md`. Estos archivos son manuales de instrucciones avanzados que la IA "lee" para aprender a realizar tareas específicas de este repositorio.
2.  **`workflows/`**: Archivos `.md` que definen pasos secuenciales para procesos técnicos (ej: despliegue, creación de casos).

---

## 🛠️ ¿Qué es un Skill?

Un **Skill** no es código ejecutable por una máquina, sino **especificaciones de alto nivel para la IA**. 

### Anatomía de un Skill (`SKILL.md`):
- **YAML Frontmatter**: Define el nombre y una descripción breve.
- **Protocolo de Actuación**: Pasos numerados que la IA debe seguir estrictamente.
- **Principios Obligatorios**: Reglas innegociables (ej: "No romper casos anteriores").
- **Lista de Verificación**: Criterios de éxito para que la IA autoevalúe su trabajo.

### Skills Disponibles Hiện nay:
- [**Crear Caso LangGraph**](.agents/skills/crear_caso/SKILL.md): Automatiza la creación de nuevos nodos, backend, frontend e integración en Docker para nuevos casos de uso.
- [**Actualizar Documentación**](.agents/skills/actualizar_doc/SKILL.md): Garantiza la sincronización total de versiones (vX.X.X) en todo el repositorio.

---

## 🔄 ¿Cómo se usan?

Cuando interactúas con un asistente habilitado para agentes en este repositorio:
1. La IA detecta que tu petición (ej: "crea un caso de finanzas") coincide con un Skill existente.
2. La IA lee el `SKILL.md` correspondiente.
3. La IA sigue el protocolo, pide aprobaciones en puntos críticos y verifica el resultado final según el estándar industrial definido.

---

## ➕ Cómo Crear un Nuevo Skill

Si identificas una tarea repetitiva y compleja, puedes "enseñarle" a la IA creando un nuevo skill:

1. Crea una carpeta en `.agents/skills/mi-nuevo-skill/`.
2. Crea un archivo `SKILL.md`.
3. Define un protocolo claro utilizando los términos técnicos del repositorio (FastAPI, Docker, Pydantic, etc.).
4. Describe los criterios de éxito ("Resultado esperado").

---

> [!TIP]
> Esta infraestructura asegura que, aunque cambie el asistente de IA o el desarrollador, los procesos de **"Misión Crítica"** del repositorio se ejecuten siempre bajo los mismos estándares de calidad.
