"""
Ingestion service — orchestrates the full PDF processing pipeline:

  PDF bytes → Extract (text + tables) → Chunk → PGVector add_documents

Every document is tagged with user_id, library_id, shelf_id, book_id
metadata for strict hierarchical context isolation during retrieval.

Uses ``LangChainChunker`` for text splitting and ``PGVector.add_documents()``
for embedding + storage (replaces manual embed → bulk_create flow).
"""

import logging
from uuid import UUID

from langchain_postgres import PGVector

from app.domain.interfaces.book_repository import IBookRepository
from app.infrastructure.database.pgvector_store import delete_documents_by_book
from app.infrastructure.ingestion.langchain_chunker import LangChainChunker
from app.infrastructure.ingestion.pdf_extractor import extract_all_from_pdf

logger = logging.getLogger(__name__)

# Maximum batch size for PGVector add_documents calls
_INGEST_BATCH_SIZE = 50


class IngestionError(Exception):
    """Raised when the ingestion pipeline fails."""


class IngestBookService:
    """
    Orchestrate document ingestion:
    1. Extract text + tables from PDF
    2. Chunk using LangChain text splitters → list[Document]
    3. Store via PGVector.add_documents (embed + persist in one call)
    4. Update book status
    """

    def __init__(
        self,
        book_repo: IBookRepository,
        vector_store: PGVector,
        chunker: LangChainChunker | None = None,
        db_session=None,
    ) -> None:
        self._book_repo = book_repo
        self._vector_store = vector_store
        self._chunker = chunker or LangChainChunker()
        self._db_session = db_session

    async def ingest(
        self,
        book_id: UUID,
        library_id: UUID,
        shelf_id: UUID | None,
        user_id: str,
        pdf_bytes: bytes,
        book_title: str = "",
        filename: str = "",
    ) -> int:
        """
        Run the full ingestion pipeline for a PDF document.

        Args:
            book_id: The book record ID.
            library_id: Parent library ID.
            shelf_id: Parent shelf ID (or None).
            user_id: Owner user ID.
            pdf_bytes: Raw PDF file bytes.
            book_title: Book title for citation metadata.
            filename: Original filename for citation metadata.

        Returns:
            Number of chunks created.

        Raises:
            IngestionError: If any step fails.
        """
        try:
            # ── Step 1: Extract text + tables ─────────────────────────
            logger.info("[Ingest] Extracting content from book %s", book_id)
            segments = extract_all_from_pdf(pdf_bytes)

            if not segments:
                logger.warning("[Ingest] No content extracted from book %s", book_id)
                await self._book_repo.update_status(book_id, "completed", 0)
                return 0

            # ── Step 2: Chunk into Document objects ───────────────────
            logger.info("[Ingest] Chunking %d segments", len(segments))
            base_metadata = {
                "user_id": user_id,
                "library_id": str(library_id),
                "shelf_id": str(shelf_id) if shelf_id else "",
                "book_id": str(book_id),
                "book_title": book_title,
                "filename": filename,
            }
            documents = self._chunker.split_segments(segments, base_metadata)

            if not documents:
                logger.warning("[Ingest] No chunks produced for book %s", book_id)
                await self._book_repo.update_status(book_id, "completed", 0)
                return 0

            # ── Step 3: Store via PGVector (embed + persist) ──────────
            logger.info("[Ingest] Storing %d documents in PGVector", len(documents))
            for i in range(0, len(documents), _INGEST_BATCH_SIZE):
                batch = documents[i : i + _INGEST_BATCH_SIZE]
                if batch:
                    await self._vector_store.aadd_documents(batch)

            # ── Step 4: Update book status ────────────────────────────
            await self._book_repo.update_status(
                book_id, "completed", len(documents)
            )

            logger.info(
                "[Ingest] ✅ Book %s ingested successfully: %d chunks",
                book_id,
                len(documents),
            )
            return len(documents)

        except Exception as e:
            logger.error("[Ingest] ❌ Failed to ingest book %s: %s", book_id, e)
            # Mark book as failed
            try:
                await self._book_repo.update_status(book_id, "failed", 0)
            except Exception:
                logger.error("[Ingest] Could not update book status to failed")
            raise IngestionError(f"Ingestion failed for book {book_id}: {e}") from e

    async def delete_book_chunks(self, book_id: UUID) -> int:
        """
        Delete all chunks belonging to a book from the vector store.

        Uses raw SQL against ``langchain_pg_embedding`` since PGVector
        doesn't have a native delete-by-metadata API.

        Args:
            book_id: The book whose chunks should be removed.

        Returns:
            Number of chunks deleted.
        """
        if self._db_session is None:
            logger.warning(
                "[Ingest] No DB session available for chunk deletion"
            )
            return 0

        return await delete_documents_by_book(self._db_session, book_id)
