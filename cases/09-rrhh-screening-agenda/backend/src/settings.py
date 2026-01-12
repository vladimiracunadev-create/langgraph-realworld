import os

from dotenv import load_dotenv


def load_settings() -> None:
    load_dotenv()


def data_dir() -> str:
    return os.getenv("DATA_DIR", "../data")
