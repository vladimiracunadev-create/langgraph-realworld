# 🚀 Hub CLI

> [!NOTE]
> **Versión**: 1.0.0 | **Estado**: Opcional/Estable | **Audiencia**: Desarrolladores, DevOps

El **Hub CLI** es una herramienta **opcional** para estandarizar el manejo de los 25 casos de este repositorio.

## 📋 Runtime Policy
Este proyecto es **Python-first**, por lo que el Hub se implementa en Python (`hub.py`) para aprovechar el ecosistema existente.
- **Sin nuevos requisitos**: Utiliza Python, que ya es necesario para los casos.
- **Opcional**: No reemplaza los flujos estándar (Docker, Make). Puedes seguir usando `docker compose up` manualmente.
- **Ligero**: Solo depende de `PyYAML` para leer los manifestos.

## 🚀 Uso Rápido

### Prerrequisitos
```bash
pip install -r requirements.txt  # Instalar PyYAML y herramientas dev
```

### Comandos
El Hub se puede invocar via `python hub.py` o los wrappers `./hub.sh` (Mac/Linux) y `hub.ps1` (Windows).

| Comando | Descripción |
|---------|-------------|
| `hub list` | Lista todos los casos y su estado (Standardized vs Legacy). |
| `hub run <ID> --input "..."` | Ejecuta el entrypoint de un caso (si está definido). |
| `hub serve <ID>` | Levanta el servidor/demo del caso (wrapper de docker compose). |
| `hub doctor` | Verifica que Python, Docker y las dependencias estén listas. |

### Integración con Make
El `Makefile` incluye atajos para usar el Hub cómodamente:

```bash
make hub-list          # Ver casos
make case-up CASE=09   # Levantar caso 09 (usa hub serve)
```

## 🛠️ Estructura de un Caso (`case.yml`)
Para que un caso sea reconocido por el Hub, debe tener un archivo `case.yml`:

```yaml
name: "Soporte Cliente Omnicanal"
slug: "soporte-cliente-omnicanal"
description: "Asistente de soporte con memoria y tools."
stack: "python-langgraph"
entrypoint: "python src/main.py"
serve: "docker compose up --build"
env:
  OPENAI_API_KEY: "required"
```
