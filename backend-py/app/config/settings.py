import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Backend Logging API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    PORT: int = int(os.getenv("PORT", 8000))

    LOG_API_ENDPOINT: str = (
        os.getenv("LOG_API_ENDPOINT") or
        "http://4.224.186.213/evaluation-service/logs"
    )
    LOG_API_KEY: str | None = os.getenv("LOG_API_KEY")
    LOG_BATCH_SIZE: int = int(os.getenv("LOG_BATCH_SIZE", 5))
    LOG_FLUSH_INTERVAL: int = int(os.getenv("LOG_FLUSH_INTERVAL", 3000))

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_NAME: str = os.getenv("DB_NAME", "appdb")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")

    CACHE_TTL: int = int(os.getenv("CACHE_TTL", 300))

    class Config:
        env_file = ".env"


settings = Settings()
