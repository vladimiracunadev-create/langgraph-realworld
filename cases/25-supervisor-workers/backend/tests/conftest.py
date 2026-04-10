"""
conftest.py — Configuración de pytest para el backend del caso 25.
"""
import os
import sys
from pathlib import Path

# Añadir el directorio backend al sys.path para importar src.*
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Configurar DATA_DIR al directorio de datos del caso
CASE_DIR = BACKEND_DIR.parent
DATA_DIR = str(CASE_DIR / "data")
os.environ.setdefault("DATA_DIR", DATA_DIR)

# Desactivar variables de entorno que podrían requerir credenciales
os.environ.setdefault("DEMO_AUTH_TOKEN", "")
os.environ.setdefault("USE_OAUTH2", "false")
