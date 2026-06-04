"""
Abstract interfaces for AI services (LLM, Embeddings, Web Search).

These live in the domain layer so the service/use-case layer
can depend on abstractions, not on LangChain or any specific provider.
"""

from abc import ABC, abstractmethod


class ILLMService(ABC):
    """Contract for LLM text generation."""

    @abstractmethod
    async def generate(self, messages: list[dict]) -> str:
        """Generate a response from a list of message dicts (role, content)."""
        ...

    @abstractmethod
    async def summarize(self, messages: list[dict]) -> str:
        """Summarize a list of messages into a concise context string."""
        ...


class IEmbeddingService(ABC):
    """Contract for text embedding generation."""

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns a list of vectors."""
        ...

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """Embed a single query string. Returns one vector."""
        ...


class IWebSearchService(ABC):
    """Contract for web search fallback (Corrective RAG)."""

    @abstractmethod
    async def search(self, query: str) -> list[dict]:
        """
        Search the web for the given query.
        Returns a list of result dicts with 'content' and 'url' keys.
        """
        ...
