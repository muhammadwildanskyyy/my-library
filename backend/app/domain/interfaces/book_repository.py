"""
Abstract interface for the Book repository.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.book import Book


class IBookRepository(ABC):
    """Contract for book persistence operations."""

    @abstractmethod
    async def create(self, book: Book) -> Book:
        """Persist a new book record."""
        ...

    @abstractmethod
    async def get_by_id(self, book_id: UUID, user_id: str) -> Book | None:
        """Find a book by ID, scoped to the user."""
        ...

    @abstractmethod
    async def list_by_library(self, library_id: UUID, user_id: str) -> list[Book]:
        """List all books in a library (any shelf or no shelf)."""
        ...

    @abstractmethod
    async def list_by_shelf(self, shelf_id: UUID, user_id: str) -> list[Book]:
        """List all books on a specific shelf."""
        ...

    @abstractmethod
    async def move_to_shelf(self, book_id: UUID, shelf_id: UUID | None, user_id: str) -> bool:
        """
        Move a book to a different shelf or back to library root (shelf_id=None).
        Returns True if successful, False if book not found.
        """
        ...

    @abstractmethod
    async def update_status(
        self, book_id: UUID, status: str, total_chunks: int
    ) -> None:
        """Update the processing status and chunk count of a book."""
        ...

    @abstractmethod
    async def update_book(
        self, book_id: UUID, user_id: str, update_data: dict
    ) -> Book | None:
        """Update book attributes. Returns updated Book, or None if not found."""
        ...


    @abstractmethod
    async def delete(self, book_id: UUID, user_id: str) -> bool:
        """Delete a book. Returns True if deleted, False if not found."""
        ...
