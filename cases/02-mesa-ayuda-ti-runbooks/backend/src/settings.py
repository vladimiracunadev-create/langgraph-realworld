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
    src/settings.py -> parents[2] = .../cases/02-mesa-ayuda-ti-runbooks
    """
    return Path(__file__).resolve().parents[2]

def backend_root() -> Path:
    """Ruta del backend del caso (cases/02-.../backend)."""
    return Path(__file__).resolve().parents[1]

def data_dir() -> str:
    """
    Define el directorio de datos (JSONs de entrada).
    """
    env = os.getenv("DATA_DIR")
    if env:
        return env
    return str(case_root() / "data")

def checkpoint_db_path() -> str:
    """Ruta del SQLite para threads (opcional si se usa in-memory o saver file)."""
    env = os.getenv("CHECKPOINT_DB")
    if env:
        return env
    return str(backend_root() / "checkpoints.sqlite")
