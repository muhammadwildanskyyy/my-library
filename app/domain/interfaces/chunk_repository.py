"""
Abstract interface for the Chunk (vector) repository.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.chunk import Chunk
from app.domain.entities.chunk_with_meta import ChunkWithMeta


class IChunkRepository(ABC):
    """Contract for chunk persistence and vector similarity search."""

    @abstractmethod
    async def bulk_create(self, chunks: list[Chunk]) -> None:
        """Insert a batch of chunks with their embeddings."""
        ...

    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: list[float],
        user_id: str,
        library_id: UUID,
        shelf_id: UUID | None = None,
        book_id: UUID | None = None,
        top_k: int = 5,
    ) -> list[Chunk]:
        """
        Find the top-k most similar chunks using cosine distance.

        CRITICAL: Always pre-filter by user_id + library_id before
        calculating vector similarity. shelf_id and book_id narrow
        the scope further when provided.
        """
        ...

    @abstractmethod
    async def similarity_search_with_metadata(
        self,
        query_embedding: list[float],
        user_id: str,
        library_id: UUID,
        shelf_id: UUID | None = None,
        book_id: UUID | None = None,
        top_k: int = 5,
    ) -> list[ChunkWithMeta]:
        """
        Find the top-k most similar chunks with source book metadata.

        Same pre-filtering as similarity_search, but JOINs to the books
        table to include book_title and filename for citation references.
        """
        ...

    @abstractmethod
    async def delete_by_book(self, book_id: UUID) -> None:
        """Delete all chunks belonging to a book."""
        ...

