"""
Central application configuration.

All values are overridable via environment variables (see .env.example).
Nothing secret is hard-coded here; defaults are safe only for local dev.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- General ---
    APP_NAME: str = "SearchForge"
    ENV: str = "development"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://searchforge:searchforge@localhost:5432/searchforge"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 600  # 10 minutes, within the 5-15 min SRS requirement

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- Search ---
    MAX_QUERY_LENGTH: int = 500
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 50
    BM25_K1: float = 1.5
    BM25_B: float = 0.75

    # --- Crawler ---
    CRAWLER_MAX_PAGES_DEFAULT: int = 50
    CRAWLER_MAX_PAGES_HARD_LIMIT: int = 500
    CRAWLER_MAX_DEPTH_DEFAULT: int = 2
    CRAWLER_MAX_DEPTH_HARD_LIMIT: int = 5
    CRAWLER_TIMEOUT_SECONDS: float = 10.0
    CRAWLER_USER_AGENT: str = "SearchForgeBot/1.0 (+https://example.com/bot)"
    CRAWLER_MAX_RETRIES: int = 2

    # --- Index persistence ---
    INDEX_STORAGE_PATH: str = "./data/index"


@lru_cache
def get_settings() -> Settings:
    return Settings()
