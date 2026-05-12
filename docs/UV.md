# Uso de `uv` en este repositorio

`uv` es el gestor de paquetes Python de [Astral](https://docs.astral.sh/uv/). Reemplaza a `pip`, `pip-tools` y `virtualenv` con una herramienta única escrita en Rust, **típicamente 10× más rápida**. En este repositorio `uv` es **opcional** — `pip` y `pip-tools` siguen siendo la vía oficial. Si lo prefieres, puedes usar `uv` como reemplazo directo en los flujos de instalación, lockfile y ejecución local de cada caso.

> [!IMPORTANT]
> **uv NO es obligatorio.** El repo funciona idéntico con `pip` puro. Esta guía describe el camino opcional con `uv` para quien quiera ejecuciones más rápidas en local.

---

## 1. Instalación de `uv`

Cualquiera de estas opciones funciona:

```bash
# Opción A — vía pip (recomendado si ya tienes Python)
pip install uv
# o
make uv-bootstrap

# Opción B — instalador oficial (independiente de Python)
# Linux / macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows PowerShell:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verifica:

```bash
uv --version
```

---

## 2. Equivalencias `pip` ↔ `uv`

| Tarea | `pip` clásico | `uv` |
|---|---|---|
| Crear entorno virtual | `python -m venv .venv` | `uv venv .venv --python 3.11` |
| Instalar requirements | `pip install -r requirements.txt` | `uv pip install -r requirements.txt` |
| Sincronizar exacto al lock | `pip install -r requirements.txt` (no exacto) | `uv pip sync requirements.txt` |
| Compilar lock desde `.in` | `pip-compile requirements.in -o requirements.txt` | `uv pip compile requirements.in -o requirements.txt` |
| Actualizar un paquete | `pip install -U pkg` | `uv pip install -U pkg` |
| Listar paquetes | `pip list` | `uv pip list` |

Las flags principales son **idénticas** a `pip-tools`/`pip`, así que no hace falta aprender nada nuevo.

---

## 3. Atajos `make` disponibles

```bash
make uv-bootstrap                # Instala uv globalmente vía pip
make uv-compile                  # Regenera requirements.txt de TODOS los casos operativos con uv pip compile
make uv-compile-check            # Verifica drift sin escribir (úsalo en CI o pre-commit)
make uv-install-case CASE=06     # Crea venv en cases/06-.../backend/.venv e instala deps con uv pip sync
```

Estos targets conviven con los pip-tools clásicos:

```bash
make pip-compile          # mismo resultado, pero más lento (pip-tools)
make pip-compile-check    # mismo drift check (pip-tools)
```

Ambos generan archivos `requirements.txt` **compatibles entre sí**: puedes regenerar con `uv` y otros desarrolladores pueden consumir con `pip` sin problemas.

---

## 4. Flujo recomendado: ejecutar un caso con `uv`

Ejemplo con el caso 06 (Compliance & Auditorías):

```bash
# 1. Instala uv una vez
pip install uv

# 2. Crea venv + instala dependencias del caso (un solo comando)
make uv-install-case CASE=06

# 3. Activa el venv
source cases/06-compliance-auditorias/backend/.venv/bin/activate
# Windows (Git Bash):
# source cases/06-compliance-auditorias/backend/.venv/Scripts/activate

# 4. Ejecuta el caso
cd cases/06-compliance-auditorias/backend
uvicorn src.api:app --port 8006
# http://localhost:8006/
```

**Comparativa típica de tiempos** en este repo (cold cache, conexión doméstica):

| Operación | `pip` | `uv` |
|---|---:|---:|
| Instalar deps de un caso (~30 paquetes) | 35–60 s | 3–6 s |
| `pip-compile` de los 18 casos operativos | 4–6 min | 25–40 s |

---

## 5. Compatibilidad con Docker, CI y lockfiles

- **Dockerfiles** del repo siguen usando `pip install --no-cache-dir -r requirements.txt`. No es necesario cambiar nada — el lockfile generado por `uv pip compile` es exactamente el mismo formato que produce `pip-compile`.
- **CI** (`.github/workflows/ci.yml`) sigue usando `pip`. Si quieres acelerarlo en una rama de prueba puedes reemplazar `pip install` por `uv pip install --system` (uv tiene modo "sistema" sin venv), pero no es obligatorio.
- **`requirements.txt`** generados por `uv` y por `pip-compile` son intercambiables. El equipo puede mezclar ambas herramientas sin conflicto.

---

## 6. Problemas comunes

| Síntoma | Solución |
|---|---|
| `uv: command not found` | `pip install uv` o reabre la terminal tras el instalador oficial |
| `uv pip sync` borra paquetes que no están en el lock | Es el comportamiento correcto: `sync` deja el venv **exactamente** como dicta el lock. Usa `uv pip install` si no quieres ese comportamiento |
| Drift inesperado entre `pip-compile` y `uv pip compile` | Ambos usan el mismo resolutor (PubGrub), pero las versiones de `pip-tools` y `uv` se actualizan a distinto ritmo. Fija una versión en CI o regenera con la misma herramienta |
| Quiero `uv run` para scripts | `uv run --with fastapi --with uvicorn -- python -m uvicorn src.api:app` ejecuta sin necesidad de venv persistente |

---

## 7. Más información

- Documentación oficial: https://docs.astral.sh/uv/
- Repositorio de uv: https://github.com/astral-sh/uv
- Comparativa de rendimiento: https://docs.astral.sh/uv/#highlights
