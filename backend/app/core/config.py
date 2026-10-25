from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ReplyLater"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database: Supports SQLite (zero-config local) or PostgreSQL + pgvector (Docker/Tiger Data)
    DATABASE_URL: str = "sqlite+aiosqlite:///./replylater.db"

    # Temporal Orchestrator
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_TASK_QUEUE: str = "email-triage-queue"

    # Local Ollama / Gemma Settings
    OLLAMA_HOST: str = "http://localhost:11434"
    GEMMA_MODEL: str = "gemma2:2b"
    FALLBACK_TO_DETERMINISTIC_MOCK: bool = True

    # Sentry Agent Tracing
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
