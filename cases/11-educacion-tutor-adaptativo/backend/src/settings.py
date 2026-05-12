from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_settings() -> None:
    load_dotenv()


def case_root() -> Path:
    """src/settings.py -> parents[2] = .../cases/11-educacion-tutor-adaptativo"""
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
