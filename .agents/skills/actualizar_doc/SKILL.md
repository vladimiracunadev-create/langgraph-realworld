---
name: Actualizar Documentación
description: Sincronizar y actualizar toda la documentación del repositorio (raíz, docs/, wiki/, casos) a una nueva versión. Usar cuando el usuario pida actualizar docs, cambiar la versión del repo, sincronizar el CHANGELOG, mejorar visualmente los markdown o reflejar cambios de seguridad/arquitectura en la documentación.
---

# Skill: Actualizar Documentación Industrial

Este skill define el protocolo para actualizar la versión y el estado de madurez de **LangGraph Realworld**
en todos sus puntos de contacto documentales, asegurando consistencia y calidad profesional.

---

## Objetivo

Asegurar que el 100% de los archivos `.md` reflejen la misma versión, taxonomía y estado de seguridad.
Incluye mejoras visuales (badges, tablas, Mermaid, callouts) y verificación de errores antes del commit.

---

## Protocolo de actuación

### 1. Auditoría de versión

Antes de editar, localizar todas las referencias a la versión anterior:

```bash
grep -rn "v3\.8\.0" --include="*.md" .
grep -rn "v3\.9\.0" --include="*.md" .
```

### 2. Sincronización del núcleo (orden de prioridad)

1. **`README.md`** raíz — badges, tabla de estados, tabla "por dónde empezar".
2. **`CHANGELOG.md`** — agregar sección de la nueva versión con cambios detallados.
3. **`ROADMAP.md`** — actualizar estado actual, mover ítems completados, agregar nuevos focos.
4. **`SECURITY.md`** — actualizar tabla de estado por capa y riesgos aceptados.
5. **`CONTRIBUTING.md`** — actualizar si cambian los estándares de Docker o código.
6. **`docs/wiki/Home.md`** — mantener en sincronía con `README.md` raíz.
7. **`docs/wiki/_Sidebar.md`** — agregar/actualizar enlaces si se crean nuevas páginas.

### 3. Sincronización de casos

Para los casos **OPERATIVO** e **INDUSTRIAL** (01, 02, 09, 10, 13):

- Actualizar versión en el encabezado: `**Versión**: X.X.0`.
- Actualizar el badge de estado si corresponde.
- Agregar referencias a cambios de seguridad o arquitectura si aplica.

Para los casos **SCAFFOLD** (03–08, 11–12, 14–25):

- Asegurar que cada README tiene: objetivo, flujo Mermaid, stack técnico y nota de scaffold.
- No declarar nada como implementado si no lo está.

### 4. Actualización del Hub CLI

Si la versión cambia, actualizar en `hub.py` el string de versión en la lógica de `list`:

```python
# Buscar y actualizar la cadena "Industrial (v3.X.X)"
```

---

## Estándares de calidad para archivos Markdown

Antes de hacer commit, verificar que cada archivo cumple:

- [ ] No hay trailing whitespace en ninguna línea.
- [ ] Cada archivo termina con exactamente un salto de línea.
- [ ] Los encabezados siguen jerarquía sin saltar niveles (`#` → `##` → `###`).
- [ ] Hay una línea en blanco antes y después de cada encabezado.
- [ ] Los bloques de código tienen lenguaje especificado (` ```bash`, ` ```python`, ` ```mermaid`).
- [ ] Los diagramas Mermaid no tienen línea en blanco tras el ` ```mermaid` de apertura.
- [ ] Los links son válidos (no apuntan a archivos inexistentes).
- [ ] Las tablas tienen alineación consistente.
- [ ] Se usan callouts de GitHub (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`) para destacar información clave.

---

## Estrategia "Surgical Match" (evitar fallos de edición)

Si un encabezado contiene caracteres especiales que causan fallos en `replace_file_content`:

1. **Divide la búsqueda** — en lugar de buscar la línea completa, busca solo la parte de texto segura.
2. **Usa contexto** — incluye la línea siguiente si es única para fijar el punto de edición.
3. **Prefiere `Write` completo** — para archivos cortos, reescribir el archivo completo evita problemas de match parcial.

---

## Verificación final

- [ ] `grep` devuelve 0 resultados para la versión anterior en archivos `.md`.
- [ ] Los badges de CI y Security en `README.md` tienen URLs correctas.
- [ ] El `CHANGELOG.md` tiene la fecha y versión actualizadas.
- [ ] Ningún README promete algo que el código aún no cumple.
- [ ] Todos los links internos entre documentos son válidos.

---

## Despliegue Git

Hacer commits semánticos separados por área:

```bash
git add README.md CHANGELOG.md ROADMAP.md SECURITY.md
git commit -m "docs(core): sincronizar documentación a vX.X.0"

git add cases/*/README.md
git commit -m "docs(cases): actualizar READMEs de casos a vX.X.0"

git add .agents/ docs/wiki/ CONTRIBUTING.md
git commit -m "docs(meta): actualizar wiki, guías y skills"
```
