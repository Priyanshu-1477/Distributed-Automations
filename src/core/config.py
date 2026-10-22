from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General Application
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "Distributed Automation Platform"
    API_V1_PREFIX: str = "/api/v1"

    # PostgreSQL Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/automation_db",
        description="Async connection URL for FastAPI async sessions",
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/automation_db",
        description="Sync connection URL for Alembic migrations and synchronous worker helpers",
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis Broker & Celery
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Operational Redis broker URL",
    )
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL",
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/1",
        description="Celery result backend URL (optional)",
    )
    CELERY_DEFAULT_QUEUE: str = "celery"
    CELERY_VISIBILITY_TIMEOUT: int = 3600  # 1 hour (must exceed max task run time)
    CELERY_TASK_TIME_LIMIT: int = 1800  # 30 minutes hard limit
    CELERY_TASK_SOFT_TIME_LIMIT: int = 1500  # 25 minutes soft limit

    # Worker Registry & Heartbeat Configuration
    HEARTBEAT_INTERVAL_SECONDS: int = 10
    STALE_TIMEOUT_SECONDS: int = 30
    OFFLINE_TIMEOUT_SECONDS: int = 90


@lru_cache
def get_settings() -> Settings:
    """Returns cached application settings instance."""
    return Settings()
