from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_settings() -> None:
    """Carga variables desde .env si existe."""
    load_dotenv()


def case_root() -> Path:
    """
    Resuelve la ruta raíz del caso de uso.
    Util para localizar archivos de datos y configuraciones específicas del módulo.
    src/settings.py -> parents[2] = .../cases/03-incident-response-sre
    """
    return Path(__file__).resolve().parents[2]


def backend_root() -> Path:
    """Ruta del backend del caso (cases/03-.../backend)."""
    return Path(__file__).resolve().parents[1]


def data_dir() -> str:
    """
    Define el directorio de datos (JSONs de entrada).
    Sustenta la portabilidad:
    1. Si existe la variable DATA_DIR (como en Docker), la usa.
    2. Si no, busca la carpeta 'data' relativa a la raíz del caso.
    """
    env = os.getenv("DATA_DIR")
    if env:
        return env
    return str(case_root() / "data")
