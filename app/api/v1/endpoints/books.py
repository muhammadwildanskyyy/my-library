"""
Book endpoints — upload (with ingestion), list, get, move, delete.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_book_service, get_current_user_id, get_ingest_service
from app.api.v1.schemas.book import BookListResponse, BookMoveRequest, BookResponse
from app.service.book_service import BookNotFoundError, BookService
from app.service.ingest_book_service import IngestBookService, IngestionError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Books"])


# ---------------------------------------------------------------------------
# Upload a book (under a library, optionally on a shelf)
# ---------------------------------------------------------------------------
@router.post(
    "/libraries/{library_id}/books/",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a book (PDF) to a library",
)
async def upload_book(
    library_id: UUID,
    file: UploadFile = File(..., description="PDF file to upload"),
    title: str = Form(..., description="Book title"),
    shelf_id: UUID | None = Form(None, description="Optional shelf ID"),
    user_id: str = Depends(get_current_user_id),
    book_svc: BookService = Depends(get_book_service),
    ingest_svc: IngestBookService = Depends(get_ingest_service),
) -> BookResponse:
    # Validate file type
    if file.content_type not in ("application/pdf",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    # Read PDF bytes
    pdf_bytes = await file.read()
    file_size = len(pdf_bytes)

    # Create book record (status='processing')
    try:
        book = await book_svc.create_book(
            user_id=user_id,
            library_id=library_id,
            title=title,
            filename=file.filename or "unknown.pdf",
            file_size=file_size,
            shelf_id=shelf_id,
        )
    except BookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # Run ingestion pipeline: extract → chunk → embed → store
    try:
        num_chunks = await ingest_svc.ingest(
            book_id=book.id,
            library_id=library_id,
            shelf_id=shelf_id,
            user_id=user_id,
            pdf_bytes=pdf_bytes,
        )
        logger.info(f"Book '{book.title}' ingested: {num_chunks} chunks")
    except IngestionError as e:
        logger.error(f"Ingestion failed for book '{book.title}': {e}")
        # Book status is set to 'failed' by IngestBookService

    # Refresh book to get updated status/chunk count
    updated_book = await book_svc.get_book(book.id, user_id)
    return _to_response(updated_book)


# ---------------------------------------------------------------------------
# List books in a library
# ---------------------------------------------------------------------------
@router.get(
    "/libraries/{library_id}/books/",
    response_model=BookListResponse,
    summary="List all books in a library",
)
async def list_books_in_library(
    library_id: UUID,
    user_id: str = Depends(get_current_user_id),
    book_svc: BookService = Depends(get_book_service),
) -> BookListResponse:
    books = await book_svc.list_books_in_library(library_id, user_id)
    return BookListResponse(
        books=[_to_response(b) for b in books],
        total=len(books),
    )


# ---------------------------------------------------------------------------
# List books on a shelf
# ---------------------------------------------------------------------------
@router.get(
    "/shelves/{shelf_id}/books/",
    response_model=BookListResponse,
    summary="List all books on a shelf",
)
async def list_books_on_shelf(
    shelf_id: UUID,
    user_id: str = Depends(get_current_user_id),
    book_svc: BookService = Depends(get_book_service),
) -> BookListResponse:
    books = await book_svc.list_books_on_shelf(shelf_id, user_id)
    return BookListResponse(
        books=[_to_response(b) for b in books],
        total=len(books),
    )


# ---------------------------------------------------------------------------
# Get a single book
# ---------------------------------------------------------------------------
@router.get(
    "/books/{book_id}",
    response_model=BookResponse,
    summary="Get a book by ID",
)
async def get_book(
    book_id: UUID,
    user_id: str = Depends(get_current_user_id),
    book_svc: BookService = Depends(get_book_service),
) -> BookResponse:
    try:
        book = await book_svc.get_book(book_id, user_id)
    except BookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _to_response(book)


# ---------------------------------------------------------------------------
# Move a book to a different shelf (or library root)
# ---------------------------------------------------------------------------
@router.patch(
    "/books/{book_id}/move",
    response_model=BookResponse,
    summary="Move a book to another shelf or library root",
)
async def move_book(
    book_id: UUID,
    body: BookMoveRequest,
    user_id: str = Depends(get_current_user_id),
    book_svc: BookService = Depends(get_book_service),
) -> BookResponse:
    try:
        book = await book_svc.move_book(book_id, body.shelf_id, user_id)
    except BookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _to_response(book)


# ---------------------------------------------------------------------------
# Delete a book
# ---------------------------------------------------------------------------
@router.delete(
    "/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book and all its chunks",
)
async def delete_book(
    book_id: UUID,
    user_id: str = Depends(get_current_user_id),
    book_svc: BookService = Depends(get_book_service),
) -> None:
    try:
        await book_svc.delete_book(book_id, user_id)
    except BookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _to_response(book) -> BookResponse:
    return BookResponse(
        id=book.id,
        library_id=book.library_id,
        shelf_id=book.shelf_id,
        user_id=UUID(book.user_id),
        title=book.title,
        filename=book.filename,
        file_size=book.file_size,
        total_chunks=book.total_chunks,
        status=book.status,
        created_at=book.created_at,
        updated_at=book.updated_at,
    )
