"""
lgrw_common.settings — Carga de .env y helpers compartidos entre los 25 backends.

Fuente canónica. NO editar las copias por caso en `cases/*/backend/src/settings.py`
directamente: editar este archivo y correr `python scripts/sync_shared.py`.

v4.15.2: superset de helpers que consumen los distintos casos (paths, LLM,
puertos, CORS, checkpoint DB, fechas y datos case-specific). Los casos con un
`settings.py` con forma radicalmente distinta (p.ej. case 13 con pydantic
BaseSettings) quedan exentos del sync.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:8080",
    "http://127.0.0.1:8080",
)


def load_settings() -> None:
    load_dotenv()


load_settings()


def case_root() -> Path:
    return Path(__file__).resolve().parents[2]


def backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    env = os.getenv("DATA_DIR")
    if env:
        return Path(env)
    return case_root() / "data"


def web_dir() -> Path:
    env = os.getenv("WEB_DIR")
    if env:
        return Path(env)
    return backend_root() / "web"


def port() -> int:
    raw = os.getenv("PORT", "8001").strip() or "8001"
    try:
        return int(raw)
    except ValueError:
        return 8001


def host() -> str:
    return os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0"


def openai_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "").strip()


def openai_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"


def use_llm() -> bool:
    return os.getenv("USE_LLM", "true").strip().lower() in {"1", "true", "yes", "on"}


def is_live_mode() -> bool:
    return use_llm() and bool(openai_api_key())


def mode_label() -> str:
    return "LIVE" if is_live_mode() else "DEMO"


def cors_allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "")
    if raw.strip():
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return list(DEFAULT_ALLOWED_ORIGINS)


def checkpoint_db_path() -> str:
    env = os.getenv("CHECKPOINT_DB")
    if env:
        return env
    return str(backend_root() / "checkpoints.sqlite")


def fecha_hoy_iso() -> str:
    """Override determinista con env FECHA_HOY=YYYY-MM-DD. Usado por case 15."""
    return os.getenv("FECHA_HOY", "2026-05-11").strip()


def pr_data_path() -> str:
    """Ruta al JSON del PR simulado. Usado por case 19."""
    env = os.getenv("PR_DATA_PATH")
    if env:
        return env
    return str(case_root() / "data" / "sample_pr.json")
