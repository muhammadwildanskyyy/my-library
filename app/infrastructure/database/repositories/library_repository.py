"""
Concrete SQLAlchemy implementation of ILibraryRepository.
"""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.library import Library
from app.domain.interfaces.library_repository import ILibraryRepository
from app.infrastructure.database.models.library_model import LibraryModel


class LibraryRepository(ILibraryRepository):
    """Persists Library entities via SQLAlchemy async session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: LibraryModel) -> Library:
        return Library(
            id=model.id,
            user_id=str(model.user_id),
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: Library) -> LibraryModel:
        return LibraryModel(
            id=entity.id,
            user_id=entity.user_id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, library: Library) -> Library:
        model = self._to_model(library)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, library_id: UUID, user_id: str) -> Library | None:
        stmt = select(LibraryModel).where(
            LibraryModel.id == library_id,
            LibraryModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_user(self, user_id: str) -> list[Library]:
        stmt = (
            select(LibraryModel)
            .where(LibraryModel.user_id == user_id)
            .order_by(LibraryModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def delete(self, library_id: UUID, user_id: str) -> bool:
        stmt = delete(LibraryModel).where(
            LibraryModel.id == library_id,
            LibraryModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0  # type: ignore[union-attr]
