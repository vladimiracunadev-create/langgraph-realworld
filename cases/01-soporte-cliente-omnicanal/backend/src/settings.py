from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def case_root() -> Path:
    return Path(__file__).resolve().parents[2]


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
    return int(os.getenv("PORT", "8001"))


def host() -> str:
    return os.getenv("HOST", "0.0.0.0")


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
