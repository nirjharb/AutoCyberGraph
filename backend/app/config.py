"""Application configuration — all secrets come from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "AutoCyberGraph"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./autocybergraph.db"
    JWT_SECRET: str = "dev-only-change-me-in-production-0123456789abcdef"
    JWT_ALGORITHM: str = "HS256"
    JWT_TTL_MINUTES: int = 60 * 8
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000"
    AI_API_KEY: str = ""
    AI_BACKEND: str = "rules"  # "rules" | "llm" (llm requires AI_API_KEY)
    STORAGE_BACKEND: str = "local"  # "local" | "s3"
    STORAGE_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 10
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_ADVISOR: str = "30/minute"
    SEED_DEMO_ON_STARTUP: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
