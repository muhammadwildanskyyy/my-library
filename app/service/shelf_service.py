"""
Shelf service — CRUD business logic for shelves within a library.
"""

from uuid import UUID

from app.domain.entities.shelf import Shelf
from app.domain.interfaces.library_repository import ILibraryRepository
from app.domain.interfaces.shelf_repository import IShelfRepository


class ShelfNotFoundError(Exception):
    """Raised when a shelf is not found or not owned by the user."""


class ShelfService:
    """Business logic for shelf management."""

    def __init__(
        self,
        shelf_repo: IShelfRepository,
        library_repo: ILibraryRepository,
    ) -> None:
        self._shelf_repo = shelf_repo
        self._library_repo = library_repo

    async def create_shelf(
        self,
        user_id: str,
        library_id: UUID,
        name: str,
        description: str | None = None,
    ) -> Shelf:
        """Create a new shelf under the specified library."""
        # Verify library ownership
        library = await self._library_repo.get_by_id(library_id, user_id)
        if not library:
            raise ShelfNotFoundError(
                f"Library '{library_id}' not found or access denied."
            )

        shelf = Shelf(
            library_id=library_id,
            user_id=user_id,
            name=name,
            description=description,
        )
        return await self._shelf_repo.create(shelf)

    async def get_shelf(self, shelf_id: UUID, user_id: str) -> Shelf:
        """Get a single shelf, ensuring it belongs to the user."""
        shelf = await self._shelf_repo.get_by_id(shelf_id, user_id)
        if not shelf:
            raise ShelfNotFoundError(
                f"Shelf '{shelf_id}' not found or access denied."
            )
        return shelf

    async def list_shelves(self, library_id: UUID, user_id: str) -> list[Shelf]:
        """List all shelves in a library owned by the user."""
        # Verify library ownership first
        library = await self._library_repo.get_by_id(library_id, user_id)
        if not library:
            raise ShelfNotFoundError(
                f"Library '{library_id}' not found or access denied."
            )
        return await self._shelf_repo.list_by_library(library_id, user_id)

    async def delete_shelf(self, shelf_id: UUID, user_id: str) -> None:
        """Delete a shelf. Books on it will have shelf_id set to NULL."""
        deleted = await self._shelf_repo.delete(shelf_id, user_id)
        if not deleted:
            raise ShelfNotFoundError(
                f"Shelf '{shelf_id}' not found or access denied."
            )
