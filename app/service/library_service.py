"""
Library service — CRUD business logic for libraries.
"""

from uuid import UUID

from app.domain.entities.library import Library
from app.domain.interfaces.library_repository import ILibraryRepository


class LibraryNotFoundError(Exception):
    """Raised when a library is not found or not owned by the user."""


class LibraryService:
    """Business logic for library management."""

    def __init__(self, library_repo: ILibraryRepository) -> None:
        self._library_repo = library_repo

    async def create_library(
        self, user_id: str, name: str, description: str | None = None
    ) -> Library:
        """Create a new library for the given user."""
        library = Library(user_id=user_id, name=name, description=description)
        return await self._library_repo.create(library)

    async def get_library(self, library_id: UUID, user_id: str) -> Library:
        """Get a single library, ensuring it belongs to the user."""
        library = await self._library_repo.get_by_id(library_id, user_id)
        if not library:
            raise LibraryNotFoundError(
                f"Library '{library_id}' not found or access denied."
            )
        return library

    async def list_libraries(self, user_id: str) -> list[Library]:
        """List all libraries owned by the user."""
        return await self._library_repo.list_by_user(user_id)

    async def delete_library(self, library_id: UUID, user_id: str) -> None:
        """Delete a library. Cascades to shelves, books, chunks."""
        deleted = await self._library_repo.delete(library_id, user_id)
        if not deleted:
            raise LibraryNotFoundError(
                f"Library '{library_id}' not found or access denied."
            )
