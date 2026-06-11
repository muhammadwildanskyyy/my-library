"""
Concrete SQLAlchemy implementation of IShelfRepository.
"""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.shelf import Shelf
from app.domain.interfaces.shelf_repository import IShelfRepository
from app.infrastructure.database.models.shelf_model import ShelfModel


class ShelfRepository(IShelfRepository):
    """Persists Shelf entities via SQLAlchemy async session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: ShelfModel) -> Shelf:
        return Shelf(
            id=model.id,
            library_id=model.library_id,
            user_id=str(model.user_id),
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: Shelf) -> ShelfModel:
        return ShelfModel(
            id=entity.id,
            library_id=entity.library_id,
            user_id=entity.user_id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, shelf: Shelf) -> Shelf:
        model = self._to_model(shelf)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, shelf_id: UUID, user_id: str) -> Shelf | None:
        stmt = select(ShelfModel).where(
            ShelfModel.id == shelf_id,
            ShelfModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_library(self, library_id: UUID, user_id: str) -> list[Shelf]:
        stmt = (
            select(ShelfModel)
            .where(
                ShelfModel.library_id == library_id,
                ShelfModel.user_id == user_id,
            )
            .order_by(ShelfModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def delete(self, shelf_id: UUID, user_id: str) -> bool:
        stmt = delete(ShelfModel).where(
            ShelfModel.id == shelf_id,
            ShelfModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0  # type: ignore[union-attr]

    async def update_shelf(
        self, shelf_id: UUID, user_id: str, update_data: dict
    ) -> Shelf | None:
        from sqlalchemy import update
        if not update_data:
            return await self.get_by_id(shelf_id, user_id)
            
        stmt = (
            update(ShelfModel)
            .where(
                ShelfModel.id == shelf_id,
                ShelfModel.user_id == user_id,
            )
            .values(**update_data)
        )
        await self._session.execute(stmt)
        await self._session.flush()
        return await self.get_by_id(shelf_id, user_id)

