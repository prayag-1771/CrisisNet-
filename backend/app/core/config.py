from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # ── Project ──
    PROJECT_NAME: str = "CrisisNet"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── Database ──
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/crisisnet"
    DATABASE_SYNC_URL: str = "postgresql://postgres:postgres@localhost:5432/crisisnet"

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Security ──
    SECRET_KEY: str = "supersecretkey_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str = "32-byte-key-change-in-production"  # AES-256 key for field-level encryption

    # ── LLM Providers ──
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # ── Agent Configuration ──
    CONFIDENCE_THRESHOLD: float = 0.75  # Below this, escalate regardless of label
    MAX_RESPONSE_RETRIES: int = 2  # Max times response generator retries on validator fail

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
