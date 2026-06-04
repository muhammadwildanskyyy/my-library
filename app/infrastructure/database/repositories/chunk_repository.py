"""
Concrete SQLAlchemy implementation of IChunkRepository with pgvector.

CRITICAL: similarity_search always pre-filters by user_id + library_id
BEFORE calculating vector cosine distance. shelf_id and book_id narrow
the scope further when provided.
"""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.chunk import Chunk
from app.domain.entities.chunk_with_meta import ChunkWithMeta
from app.domain.interfaces.chunk_repository import IChunkRepository
from app.infrastructure.database.models.book_model import BookModel
from app.infrastructure.database.models.chunk_model import ChunkModel


class ChunkRepository(IChunkRepository):
    """Chunk persistence with pgvector similarity search."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: ChunkModel) -> Chunk:
        return Chunk(
            id=model.id,
            book_id=model.book_id,
            library_id=model.library_id,
            shelf_id=model.shelf_id,
            user_id=str(model.user_id),
            content=model.content,
            chunk_index=model.chunk_index,
            token_count=model.token_count,
            embedding=list(model.embedding) if model.embedding is not None else [],
            source_type=model.source_type,
            created_at=model.created_at,
        )

    async def bulk_create(self, chunks: list[Chunk]) -> None:
        """Insert a batch of chunks with their embeddings."""
        models = []
        for chunk in chunks:
            model = ChunkModel(
                id=chunk.id,
                book_id=chunk.book_id,
                library_id=chunk.library_id,
                shelf_id=chunk.shelf_id,
                user_id=chunk.user_id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                token_count=chunk.token_count,
                embedding=chunk.embedding,
                source_type=chunk.source_type,
                created_at=chunk.created_at,
            )
            models.append(model)

        self._session.add_all(models)
        await self._session.flush()

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

        CRITICAL: Always pre-filters by user_id + library_id before
        calculating vector similarity. This ensures absolute context
        isolation per user and per hierarchy level.
        """
        # Build base query with mandatory filters
        stmt = select(ChunkModel).where(
            ChunkModel.user_id == user_id,
            ChunkModel.library_id == library_id,
        )

        # Optional narrowing filters
        if shelf_id is not None:
            stmt = stmt.where(ChunkModel.shelf_id == shelf_id)

        if book_id is not None:
            stmt = stmt.where(ChunkModel.book_id == book_id)

        # Order by cosine distance (ascending = most similar first)
        stmt = stmt.order_by(
            ChunkModel.embedding.cosine_distance(query_embedding)
        ).limit(top_k)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(m) for m in models]

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

        JOINs chunks → books to include book_title and filename
        for building citation references in RAG answers.
        """
        # SELECT chunks + book title/filename via JOIN
        stmt = (
            select(ChunkModel, BookModel.title, BookModel.filename)
            .join(BookModel, ChunkModel.book_id == BookModel.id)
            .where(
                ChunkModel.user_id == user_id,
                ChunkModel.library_id == library_id,
            )
        )

        # Optional narrowing filters
        if shelf_id is not None:
            stmt = stmt.where(ChunkModel.shelf_id == shelf_id)

        if book_id is not None:
            stmt = stmt.where(ChunkModel.book_id == book_id)

        # Order by cosine distance (ascending = most similar first)
        stmt = stmt.order_by(
            ChunkModel.embedding.cosine_distance(query_embedding)
        ).limit(top_k)

        result = await self._session.execute(stmt)
        rows = result.all()

        return [
            ChunkWithMeta(
                chunk_id=row[0].id,
                book_id=row[0].book_id,
                book_title=row[1],       # BookModel.title
                filename=row[2],          # BookModel.filename
                chunk_index=row[0].chunk_index,
                source_type=row[0].source_type,
                content=row[0].content,
            )
            for row in rows
        ]

    async def delete_by_book(self, book_id: UUID) -> None:
        """Delete all chunks belonging to a book."""
        stmt = delete(ChunkModel).where(ChunkModel.book_id == book_id)
        await self._session.execute(stmt)

