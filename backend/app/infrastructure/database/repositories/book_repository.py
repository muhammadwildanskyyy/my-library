"""
Concrete SQLAlchemy implementation of IBookRepository.
"""

from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.book import Book
from app.domain.interfaces.book_repository import IBookRepository
from app.infrastructure.database.models.book_model import BookModel


class BookRepository(IBookRepository):
    """Persists Book entities via SQLAlchemy async session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: BookModel) -> Book:
        return Book(
            id=model.id,
            library_id=model.library_id,
            shelf_id=model.shelf_id,
            user_id=str(model.user_id),
            title=model.title,
            filename=model.filename,
            file_url=model.file_url,
            file_size=model.file_size,
            total_chunks=model.total_chunks,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: Book) -> BookModel:
        return BookModel(
            id=entity.id,
            library_id=entity.library_id,
            shelf_id=entity.shelf_id,
            user_id=entity.user_id,
            title=entity.title,
            filename=entity.filename,
            file_url=entity.file_url,
            file_size=entity.file_size,
            total_chunks=entity.total_chunks,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, book: Book) -> Book:
        model = self._to_model(book)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, book_id: UUID, user_id: str) -> Book | None:
        stmt = select(BookModel).where(
            BookModel.id == book_id,
            BookModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_library(self, library_id: UUID, user_id: str) -> list[Book]:
        stmt = (
            select(BookModel)
            .where(
                BookModel.library_id == library_id,
                BookModel.user_id == user_id,
            )
            .order_by(BookModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_shelf(self, shelf_id: UUID, user_id: str) -> list[Book]:
        stmt = (
            select(BookModel)
            .where(
                BookModel.shelf_id == shelf_id,
                BookModel.user_id == user_id,
            )
            .order_by(BookModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def move_to_shelf(
        self, book_id: UUID, shelf_id: UUID | None, user_id: str
    ) -> bool:
        stmt = (
            update(BookModel)
            .where(
                BookModel.id == book_id,
                BookModel.user_id == user_id,
            )
            .values(shelf_id=shelf_id)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0  # type: ignore[union-attr]

    async def update_status(
        self, book_id: UUID, status: str, total_chunks: int
    ) -> None:
        stmt = (
            update(BookModel)
            .where(BookModel.id == book_id)
            .values(status=status, total_chunks=total_chunks)
        )
        await self._session.execute(stmt)

    async def delete(self, book_id: UUID, user_id: str) -> bool:
        stmt = delete(BookModel).where(
            BookModel.id == book_id,
            BookModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        
        # If the book was successfully deleted, manually clean up its vector chunks
        if result.rowcount > 0:  # type: ignore[union-attr]
            from sqlalchemy import text
            await self._session.execute(
                text("DELETE FROM langchain_pg_embedding WHERE cmetadata->>'book_id' = :book_id"),
                {"book_id": str(book_id)}
            )
            
        return result.rowcount > 0  # type: ignore[union-attr]

    async def update_book(
        self, book_id: UUID, user_id: str, update_data: dict
    ) -> Book | None:
        if not update_data:
            return await self.get_by_id(book_id, user_id)
            
        stmt = (
            update(BookModel)
            .where(
                BookModel.id == book_id,
                BookModel.user_id == user_id,
            )
            .values(**update_data)
        )
        await self._session.execute(stmt)
        await self._session.flush()
        return await self.get_by_id(book_id, user_id)


    async def get_chunks_by_book_id(
        self, book_id: UUID, user_id: str
    ) -> list[dict]:
        """
        Retrieve all text chunks for a book from the PGVector embedding table.

        Queries ``langchain_pg_embedding`` directly, filtered by both
        ``book_id`` and ``user_id`` in the JSONB metadata for security.
        Returns chunks sorted by ``chunk_index`` ascending.

        Args:
            book_id: The book whose chunks to retrieve.
            user_id: Must match the chunk's ``user_id`` metadata (ownership check).

        Returns:
            List of dicts with chunk_index, content, source_type, page, token_count.
        """
        from sqlalchemy import text

        result = await self._session.execute(
            text("""
                SELECT
                    (e.cmetadata->>'chunk_index')::int   AS chunk_index,
                    e.document                           AS content,
                    COALESCE(e.cmetadata->>'source_type', 'text') AS source_type,
                    COALESCE(e.cmetadata->>'page', '0')  AS page,
                    COALESCE(e.cmetadata->>'token_count', '0') AS token_count
                FROM langchain_pg_embedding e
                WHERE e.cmetadata->>'book_id'  = :book_id
                  AND e.cmetadata->>'user_id'  = :user_id
                ORDER BY (e.cmetadata->>'chunk_index')::int ASC
            """),
            {"book_id": str(book_id), "user_id": str(user_id)},
        )
        rows = result.fetchall()
        return [
            {
                "chunk_index": row.chunk_index,
                "content": row.content,
                "source_type": row.source_type,
                "page": row.page,
                "token_count": row.token_count,
            }
            for row in rows
        ]
