import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///../data/bi_database.sqlite")
    PORT: int = int(os.getenv("PORT", 8013))
    HOST: str = os.getenv("HOST", "0.0.0.0")

settings = Settings()
