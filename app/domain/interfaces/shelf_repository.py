"""
Abstract interface for the Shelf repository.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.shelf import Shelf


class IShelfRepository(ABC):
    """Contract for shelf persistence operations."""

    @abstractmethod
    async def create(self, shelf: Shelf) -> Shelf:
        """Persist a new shelf."""
        ...

    @abstractmethod
    async def get_by_id(self, shelf_id: UUID, user_id: str) -> Shelf | None:
        """Find a shelf by ID, scoped to the user."""
        ...

    @abstractmethod
    async def list_by_library(self, library_id: UUID, user_id: str) -> list[Shelf]:
        """List all shelves in a library, scoped to the user."""
        ...

    @abstractmethod
    async def delete(self, shelf_id: UUID, user_id: str) -> bool:
        """Delete a shelf. Returns True if deleted, False if not found."""
        ...
