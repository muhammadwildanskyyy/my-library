"""
Application settings loaded from environment variables / .env file.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the AI Librarian Platform."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database -----------------------------------------------------------
    DATABASE_URL: str = (
        "postgresql+asyncpg://librarian:librarian_secret@db:5432/ai_librarian"
    )

    # --- JWT Auth -----------------------------------------------------------
    JWT_SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Active LLM ---------------------------------------------------------
    ACTIVE_MODEL: Literal["openai", "gemini"] = "openai"

    # --- API Keys -----------------------------------------------------------
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    TAVILY_API_KEY: str = ""

    # --- Embedding ----------------------------------------------------------
    EMBEDDING_DIMENSIONS: int = 1536
    EMBEDDING_MODEL: Literal["openai", "gemini"] = "openai"

    # --- Chunking -----------------------------------------------------------
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    # --- Chat Memory --------------------------------------------------------
    SLIDING_WINDOW_TOKEN_LIMIT: int = 4000
    SLIDING_WINDOW_SUMMARIZE_COUNT: int = 10


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — avoids re-reading .env on every request."""
    return Settings()
