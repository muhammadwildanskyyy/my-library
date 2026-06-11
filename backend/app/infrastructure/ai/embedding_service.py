"""
Concrete implementation of IEmbeddingService using LangChain embeddings.

Supports both OpenAI and Google embedding models based on EMBEDDING_MODEL config.
"""

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings

from app.config.settings import Settings, get_settings
from app.domain.interfaces.ai_service import IEmbeddingService


class EmbeddingService(IEmbeddingService):
    """Generate text embeddings using OpenAI or Google models."""

    def __init__(self, settings: Settings | None = None) -> None:
        s = settings or get_settings()
        self._embedder = self._create_embedder(s)

    @staticmethod
    def _create_embedder(s: Settings):
        if s.EMBEDDING_MODEL == "openai":
            return OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=s.OPENAI_API_KEY,  # type: ignore[arg-type]
                dimensions=s.EMBEDDING_DIMENSIONS,
            )
        elif s.EMBEDDING_MODEL == "gemini":
            return GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-2",
                google_api_key=s.GOOGLE_API_KEY,  # type: ignore[arg-type]
            )
        else:
            raise ValueError(
                f"Unknown EMBEDDING_MODEL '{s.EMBEDDING_MODEL}'. "
                "Expected 'openai' or 'gemini'."
            )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns a list of vectors."""
        return await self._embedder.aembed_documents(texts)

    async def embed_query(self, query: str) -> list[float]:
        """Embed a single query string. Returns one vector."""
        return await self._embedder.aembed_query(query)
