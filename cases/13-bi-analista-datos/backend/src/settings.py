import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


def backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def case_root() -> Path:
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///../data/bi_database.sqlite")
    PORT: int = int(os.getenv("PORT", 8013))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    @property
    def data_dir(self) -> Path:
        env = os.getenv("DATA_DIR")
        if env:
            return Path(env)
        return case_root() / "data"

    @property
    def database_path(self) -> Path:
        url = self.DATABASE_URL
        if url.startswith("sqlite:///"):
            raw_path = url.replace("sqlite:///", "", 1)
            candidate = Path(raw_path)
            if candidate.is_absolute():
                return candidate
            return (backend_root() / candidate).resolve()
        return (self.data_dir / "bi_database.sqlite").resolve()

    @property
    def web_dir(self) -> Path:
        env = os.getenv("WEB_DIR")
        if env:
            return Path(env)
        return case_root() / "web"


settings = Settings()
