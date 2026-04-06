from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8002",
    "http://127.0.0.1:8002",
)


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


def cors_allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "")
    if raw.strip():
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return list(DEFAULT_ALLOWED_ORIGINS)
