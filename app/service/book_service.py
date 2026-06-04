"""
Book service — CRUD and move business logic for books.

NOTE: Actual PDF ingestion (chunking + embedding) is handled by
IngestBookService in Step 3. This service only manages the book
record and file metadata.
"""

from uuid import UUID

from app.domain.entities.book import Book
from app.domain.interfaces.book_repository import IBookRepository
from app.domain.interfaces.library_repository import ILibraryRepository
from app.domain.interfaces.shelf_repository import IShelfRepository


class BookNotFoundError(Exception):
    """Raised when a book is not found or not owned by the user."""


class BookService:
    """Business logic for book record management."""

    def __init__(
        self,
        book_repo: IBookRepository,
        library_repo: ILibraryRepository,
        shelf_repo: IShelfRepository,
    ) -> None:
        self._book_repo = book_repo
        self._library_repo = library_repo
        self._shelf_repo = shelf_repo

    async def create_book(
        self,
        user_id: str,
        library_id: UUID,
        title: str,
        filename: str,
        file_size: int,
        shelf_id: UUID | None = None,
    ) -> Book:
        """
        Create a book record (status='processing').

        The caller is responsible for triggering the ingestion pipeline
        after this method returns.
        """
        # Verify library ownership
        library = await self._library_repo.get_by_id(library_id, user_id)
        if not library:
            raise BookNotFoundError(
                f"Library '{library_id}' not found or access denied."
            )

        # Verify shelf ownership if provided
        if shelf_id:
            shelf = await self._shelf_repo.get_by_id(shelf_id, user_id)
            if not shelf:
                raise BookNotFoundError(
                    f"Shelf '{shelf_id}' not found or access denied."
                )

        book = Book(
            library_id=library_id,
            shelf_id=shelf_id,
            user_id=user_id,
            title=title,
            filename=filename,
            file_size=file_size,
            status="processing",
        )
        return await self._book_repo.create(book)

    async def get_book(self, book_id: UUID, user_id: str) -> Book:
        """Get a single book, ensuring it belongs to the user."""
        book = await self._book_repo.get_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(
                f"Book '{book_id}' not found or access denied."
            )
        return book

    async def list_books_in_library(
        self, library_id: UUID, user_id: str
    ) -> list[Book]:
        """List all books in a library (any shelf or no shelf)."""
        return await self._book_repo.list_by_library(library_id, user_id)

    async def list_books_on_shelf(
        self, shelf_id: UUID, user_id: str
    ) -> list[Book]:
        """List all books on a specific shelf."""
        return await self._book_repo.list_by_shelf(shelf_id, user_id)

    async def move_book(
        self, book_id: UUID, shelf_id: UUID | None, user_id: str
    ) -> Book:
        """
        Move a book to a different shelf or back to library root.

        Args:
            book_id: The book to move.
            shelf_id: Target shelf, or None to move to library root.
            user_id: Current user.

        Returns:
            The updated book entity.
        """
        # Verify book ownership
        book = await self._book_repo.get_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(
                f"Book '{book_id}' not found or access denied."
            )

        # Verify target shelf if provided
        if shelf_id:
            shelf = await self._shelf_repo.get_by_id(shelf_id, user_id)
            if not shelf:
                raise BookNotFoundError(
                    f"Shelf '{shelf_id}' not found or access denied."
                )

        await self._book_repo.move_to_shelf(book_id, shelf_id, user_id)

        # Return refreshed entity
        updated = await self._book_repo.get_by_id(book_id, user_id)
        assert updated is not None
        return updated

    async def delete_book(self, book_id: UUID, user_id: str) -> None:
        """Delete a book and all its chunks (cascaded)."""
        deleted = await self._book_repo.delete(book_id, user_id)
        if not deleted:
            raise BookNotFoundError(
                f"Book '{book_id}' not found or access denied."
            )
