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
    src/settings.py -> parents[2] = .../cases/19-devex-pr-review
    """
    return Path(__file__).resolve().parents[2]


def backend_root() -> Path:
    """Ruta del backend del caso (cases/19-.../backend)."""
    return Path(__file__).resolve().parents[1]


def pr_data_path() -> str:
    """
    Ruta al JSON del PR simulado.
    Prioridad:
    1. Si existe la variable PR_DATA_PATH (como en Docker), la usa.
    2. Si no, busca sample_pr.json en la carpeta 'data' relativa a la raíz del caso.
    """
    env = os.getenv("PR_DATA_PATH")
    if env:
        return env
    return str(case_root() / "data" / "sample_pr.json")


def checkpoint_db_path() -> str:
    """Ruta del SQLite de checkpoints (LangGraph).

    Prioridad:
    1) env CHECKPOINT_DB
    2) <backend_root>/checkpoints.sqlite
    """
    env = os.getenv("CHECKPOINT_DB")
    if env:
        return env
    return str(backend_root() / "checkpoints.sqlite")
