"""
LangChain PGVector store factory.

Creates a ``langchain_postgres.PGVector`` instance that stores document
embeddings in the ``langchain_pg_embedding`` table.  This coexists with
the async SQLAlchemy engine used for regular CRUD — it uses a separate
``psycopg3`` connection string.

Usage::

    store = create_pgvector_store(embeddings)
    await store.aadd_documents(documents)
    retriever = store.as_retriever(search_kwargs={...})
"""

from __future__ import annotations

import logging
from uuid import UUID

from langchain_core.embeddings import Embeddings
from langchain_postgres import PGVector
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def create_pgvector_store(
    embeddings: Embeddings,
    settings: Settings | None = None,
) -> PGVector:
    """
    Create a LangChain PGVector store backed by PostgreSQL.

    The store manages its own tables (``langchain_pg_collection``,
    ``langchain_pg_embedding``) and uses ``psycopg3`` for connectivity.

    Args:
        embeddings: LangChain embeddings model for vectorisation.
        settings: Optional settings override (uses singleton otherwise).

    Returns:
        Configured PGVector instance ready for add/search operations.
    """
    s = settings or get_settings()

    return PGVector(
        embeddings=embeddings,
        collection_name=s.PGVECTOR_COLLECTION_NAME,
        connection=s.DATABASE_URL,
        use_jsonb=True,
        async_mode=True,
        create_extension=False,
    )


async def delete_documents_by_metadata(
    session: AsyncSession,
    collection_name: str,
    metadata_filter: dict[str, str],
) -> int:
    """
    Delete documents from ``langchain_pg_embedding`` matching a metadata filter.

    Used when a book is deleted — removes all its chunks from the vector store.

    Args:
        session: Active async SQLAlchemy session.
        collection_name: PGVector collection name.
        metadata_filter: Key-value pairs to match in ``cmetadata`` JSONB.

    Returns:
        Number of rows deleted.
    """
    import json

    filter_json = json.dumps(metadata_filter)

    result = await session.execute(
        text("""
            DELETE FROM langchain_pg_embedding e
            USING langchain_pg_collection c
            WHERE e.collection_id = c.uuid
              AND c.name = :collection_name
              AND e.cmetadata @> :filter_json::jsonb
        """),
        {"collection_name": collection_name, "filter_json": filter_json},
    )

    deleted = result.rowcount  # type: ignore[union-attr]
    logger.info(
        "[PGVector] Deleted %d documents matching %s from collection '%s'",
        deleted,
        metadata_filter,
        collection_name,
    )
    return deleted


async def delete_documents_by_book(
    session: AsyncSession,
    book_id: UUID,
    collection_name: str | None = None,
) -> int:
    """
    Convenience wrapper — delete all chunks belonging to a specific book.

    Args:
        session: Active async SQLAlchemy session.
        book_id: The book whose chunks should be removed.
        collection_name: PGVector collection (defaults to settings value).
    """
    s = get_settings()
    coll = collection_name or s.PGVECTOR_COLLECTION_NAME
    return await delete_documents_by_metadata(
        session, coll, {"book_id": str(book_id)}
    )
