"""
Abstract interface for the Library repository.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.library import Library


class ILibraryRepository(ABC):
    """Contract for library persistence operations."""

    @abstractmethod
    async def create(self, library: Library) -> Library:
        """Persist a new library."""
        ...

    @abstractmethod
    async def get_by_id(self, library_id: UUID, user_id: str) -> Library | None:
        """Find a library by ID, scoped to the user."""
        ...

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[Library]:
        """List all libraries owned by a user."""
        ...

    @abstractmethod
    async def update_library(
        self, library_id: UUID, user_id: str, update_data: dict
    ) -> Library | None:
        """Update library attributes. Returns updated Library, or None if not found."""
        ...


    @abstractmethod
    async def delete(self, library_id: UUID, user_id: str) -> bool:
        """Delete a library. Returns True if deleted, False if not found."""
        ...
