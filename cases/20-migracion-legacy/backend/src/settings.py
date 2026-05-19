"""
lgrw_common.settings — Carga de .env y helpers de paths (case_root, data_dir, web_dir).

Fuente canónica compartida entre los 25 backends. NO editar las copias por caso
en `cases/*/backend/src/settings.py` directamente: editar este archivo y correr
`python scripts/sync_shared.py` para propagar.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_settings() -> None:
    load_dotenv()


def case_root() -> Path:
    return Path(__file__).resolve().parents[2]


def backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_dir() -> str:
    env = os.getenv("DATA_DIR")
    if env:
        return env
    return str(case_root() / "data")


def web_dir() -> Path:
    env = os.getenv("WEB_DIR")
    if env:
        return Path(env)
    return backend_root() / "web"
