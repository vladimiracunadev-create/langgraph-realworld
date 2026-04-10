"""
conftest.py — Configuración global de pytest para el caso 19.

Configura sys.path y las variables de entorno necesarias
para ejecutar los tests sin necesidad de Docker ni credenciales reales.
"""
import os
import sys
from pathlib import Path

# Asegurar que src/ sea importable desde los tests
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ruta al directorio de datos del caso (../data relativo al backend)
CASE_DIR = BACKEND_DIR.parent
DATA_DIR = CASE_DIR / "data"

# Configurar variables de entorno para modo DEMO
os.environ.setdefault("PR_DATA_PATH", str(DATA_DIR / "sample_pr.json"))
os.environ.setdefault("CHECKPOINT_DB", ":memory:")

# Asegurarse de NO usar credenciales reales en tests
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("GITHUB_TOKEN", None)
os.environ.pop("DEMO_AUTH_TOKEN", None)
