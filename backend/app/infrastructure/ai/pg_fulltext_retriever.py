"""
PostgreSQL Full-Text Search retriever for ``langchain_pg_embedding``.

Implements lexical keyword search using ``to_tsvector`` / ``plainto_tsquery``
directly against the LangChain PGVector embedding table.  This is paired
with the PGVector semantic retriever inside an ``EnsembleRetriever`` to
give hybrid (semantic + keyword) retrieval.

Pre-filtering by user/library/shelf metadata ensures context isolation.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)

# Metadata keys that are safe to use in SQL filter construction
_ALLOWED_FILTER_KEYS = frozenset(
    {"user_id", "library_id", "shelf_id", "book_id"}
)


class PGFullTextSearchRetriever(BaseRetriever):
    """
    LangChain retriever backed by PostgreSQL full-text search.

    Queries the ``langchain_pg_embedding`` table using ``plainto_tsquery``
    and ranks results with ``ts_rank``.  Metadata filtering is applied via
    JSONB containment (``@>``) for context isolation.

    **Important**: This retriever is async-only.  The synchronous
    ``_get_relevant_documents`` raises ``NotImplementedError``.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_factory: async_sessionmaker = Field(
        ..., description="SQLAlchemy async session factory"
    )
    collection_name: str = Field(
        ..., description="PGVector collection to search"
    )
    k: int = Field(default=10, description="Maximum documents to return")
    filter_metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Metadata key-value filters for context isolation",
    )

    # -- Sync (required by ABC but we only use async) ----------------------
    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> list[Document]:
        raise NotImplementedError(
            "PGFullTextSearchRetriever is async-only. Use ainvoke() instead."
        )

    # -- Async (the real implementation) -----------------------------------
    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Any = None,
    ) -> list[Document]:
        """
        Execute a PostgreSQL full-text search against the embedding table.

        Steps:
        1. Join ``langchain_pg_embedding`` ← ``langchain_pg_collection``
        2. Apply JSONB containment filter for context isolation
        3. Match with ``plainto_tsquery``
        4. Rank by ``ts_rank`` descending
        5. Return top-k as ``Document`` objects
        """
        if not query.strip():
            return []

        # Build the JSONB containment filter
        filter_dict = {
            k: v
            for k, v in self.filter_metadata.items()
            if k in _ALLOWED_FILTER_KEYS
        }
        filter_json = json.dumps(filter_dict) if filter_dict else "{}"

        sql = text("""
            SELECT e.document, e.cmetadata
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = :collection_name
              AND e.cmetadata @> :filter_json ::jsonb
              AND to_tsvector('english', e.document)
                  @@ plainto_tsquery('english', :query)
            ORDER BY ts_rank(
                to_tsvector('english', e.document),
                plainto_tsquery('english', :query)
            ) DESC
            LIMIT :k
        """)

        async with self.session_factory() as session:
            result = await session.execute(
                sql,
                {
                    "collection_name": self.collection_name,
                    "filter_json": filter_json,
                    "query": query,
                    "k": self.k,
                },
            )
            rows = result.all()

        docs = [
            Document(
                page_content=row[0],
                metadata=row[1] if isinstance(row[1], dict) else {},
            )
            for row in rows
        ]

        logger.info(
            "[FTS] Query '%s…' → %d results (collection=%s, filter=%s)",
            query[:60],
            len(docs),
            self.collection_name,
            filter_dict,
        )
        return docs
