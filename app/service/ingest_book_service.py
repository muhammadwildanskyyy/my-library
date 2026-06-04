"""
Ingestion service — orchestrates the full PDF processing pipeline:

  PDF bytes → Extract (text + tables) → Chunk → Embed → Store in pgvector

Every chunk is tagged with user_id, library_id, shelf_id, book_id
for strict hierarchical context isolation.
"""

import logging
from uuid import UUID

from app.domain.entities.chunk import Chunk
from app.domain.interfaces.ai_service import IEmbeddingService
from app.domain.interfaces.book_repository import IBookRepository
from app.domain.interfaces.chunk_repository import IChunkRepository
from app.infrastructure.ingestion.chunker import TiktokenChunker
from app.infrastructure.ingestion.pdf_extractor import extract_all_from_pdf

logger = logging.getLogger(__name__)

# Maximum batch size for embedding API calls
_EMBED_BATCH_SIZE = 50


class IngestionError(Exception):
    """Raised when the ingestion pipeline fails."""


class IngestBookService:
    """
    Orchestrate document ingestion:
    1. Extract text + tables from PDF
    2. Chunk using tiktoken
    3. Generate embeddings
    4. Bulk insert chunks with metadata into pgvector
    5. Update book status
    """

    def __init__(
        self,
        book_repo: IBookRepository,
        chunk_repo: IChunkRepository,
        embedding_service: IEmbeddingService,
        chunker: TiktokenChunker | None = None,
    ) -> None:
        self._book_repo = book_repo
        self._chunk_repo = chunk_repo
        self._embedding_service = embedding_service
        self._chunker = chunker or TiktokenChunker()

    async def ingest(
        self,
        book_id: UUID,
        library_id: UUID,
        shelf_id: UUID | None,
        user_id: str,
        pdf_bytes: bytes,
    ) -> int:
        """
        Run the full ingestion pipeline for a PDF document.

        Args:
            book_id: The book record ID.
            library_id: Parent library ID.
            shelf_id: Parent shelf ID (or None).
            user_id: Owner user ID.
            pdf_bytes: Raw PDF file bytes.

        Returns:
            Number of chunks created.

        Raises:
            IngestionError: If any step fails.
        """
        try:
            # ── Step 1: Extract text + tables ─────────────────────────
            logger.info(f"[Ingest] Extracting content from book {book_id}")
            segments = extract_all_from_pdf(pdf_bytes)

            if not segments:
                logger.warning(f"[Ingest] No content extracted from book {book_id}")
                await self._book_repo.update_status(book_id, "completed", 0)
                return 0

            # ── Step 2: Chunk ─────────────────────────────────────────
            logger.info(f"[Ingest] Chunking {len(segments)} segments")
            chunked = self._chunker.chunk_segments(segments)

            if not chunked:
                logger.warning(f"[Ingest] No chunks produced for book {book_id}")
                await self._book_repo.update_status(book_id, "completed", 0)
                return 0

            # ── Step 3: Embed in batches ──────────────────────────────
            logger.info(f"[Ingest] Embedding {len(chunked)} chunks")
            texts = [c["content"] for c in chunked]
            all_embeddings: list[list[float]] = []

            for i in range(0, len(texts), _EMBED_BATCH_SIZE):
                batch = texts[i : i + _EMBED_BATCH_SIZE]
                batch_embeddings = await self._embedding_service.embed_texts(batch)
                all_embeddings.extend(batch_embeddings)

            # ── Step 4: Build chunk entities ──────────────────────────
            chunk_entities: list[Chunk] = []
            for idx, (chunk_data, embedding) in enumerate(
                zip(chunked, all_embeddings)
            ):
                chunk = Chunk(
                    book_id=book_id,
                    library_id=library_id,
                    shelf_id=shelf_id,
                    user_id=user_id,
                    content=chunk_data["content"],
                    chunk_index=idx,
                    token_count=chunk_data["token_count"],
                    embedding=embedding,
                    source_type=chunk_data.get("source_type", "text"),
                )
                chunk_entities.append(chunk)

            # ── Step 5: Bulk insert into pgvector ─────────────────────
            logger.info(f"[Ingest] Storing {len(chunk_entities)} chunks in pgvector")
            await self._chunk_repo.bulk_create(chunk_entities)

            # ── Step 6: Update book status ────────────────────────────
            await self._book_repo.update_status(
                book_id, "completed", len(chunk_entities)
            )

            logger.info(
                f"[Ingest] ✅ Book {book_id} ingested successfully: "
                f"{len(chunk_entities)} chunks"
            )
            return len(chunk_entities)

        except Exception as e:
            logger.error(f"[Ingest] ❌ Failed to ingest book {book_id}: {e}")
            # Mark book as failed
            try:
                await self._book_repo.update_status(book_id, "failed", 0)
            except Exception:
                logger.error(f"[Ingest] Could not update book status to failed")
            raise IngestionError(f"Ingestion failed for book {book_id}: {e}") from e
