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
        return result.rowcount > 0  # type: ignore[union-attr]
