"""
Application settings loaded from environment variables / .env file.
"""

from functools import lru_cache
from typing import Literal

from pydantic import computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the AI Librarian Platform."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Environment & Security ---------------------------------------------
    ENVIRONMENT: Literal["development", "production"] = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # --- Database -----------------------------------------------------------
    DATABASE_URL: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Derive psycopg3 connection string from the asyncpg one.

        langchain_postgres.PGVector requires ``postgresql+psycopg://`` while
        our SQLAlchemy async engine uses ``postgresql+asyncpg://``.
        """
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg")

    # --- JWT Auth -----------------------------------------------------------
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Active LLM ---------------------------------------------------------
    ACTIVE_MODEL: Literal["openai", "gemini"] = "openai"

    # --- API Keys -----------------------------------------------------------
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    TAVILY_API_KEY: str
    CLOUDINARY_URL: str

    # --- Embedding ----------------------------------------------------------
    EMBEDDING_DIMENSIONS: int = 1536
    EMBEDDING_MODEL: Literal["openai", "gemini"] = "openai"

    # --- Chunking -----------------------------------------------------------
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    CHUNK_STRATEGY: Literal["token", "recursive"] = "recursive"

    # --- Retrieval ----------------------------------------------------------
    RETRIEVER_VECTOR_TOP_K: int = 10
    RETRIEVER_FTS_TOP_K: int = 10
    RETRIEVER_ENSEMBLE_WEIGHTS: list[float] = [0.5, 0.5]
    RERANKER_TOP_N: int = 5

    # --- LangChain Postgres -------------------------------------------------
    PGVECTOR_COLLECTION_NAME: str = "ai_librarian_chunks"

    # --- Chat Memory --------------------------------------------------------
    SLIDING_WINDOW_TOKEN_LIMIT: int = 4000
    SLIDING_WINDOW_SUMMARIZE_COUNT: int = 10

    # --- Cache --------------------------------------------------------------
    ENABLE_LLM_CACHE: bool = False

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if self.JWT_SECRET_KEY == "change-me-to-a-random-64-char-string":
                raise ValueError("JWT_SECRET_KEY must be changed in production")
            if "*" in self.CORS_ORIGINS:
                raise ValueError("CORS_ORIGINS cannot contain '*' in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — avoids re-reading .env on every request."""
    return Settings()

