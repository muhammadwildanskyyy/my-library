"""
Retrieval pipeline factory — builds the multi-stage retriever stack.

Architecture::

    ┌─────────────────────────────────────────────┐
    │  create_history_aware_retriever (LLM)       │
    │  → reformulates query from chat history     │
    │                                             │
    │   ┌─────────────────────────────────────┐   │
    │   │ ContextualCompressionRetriever      │   │
    │   │ → FlashrankRerank (top_n)           │   │
    │   │                                     │   │
    │   │  ┌──────────────────────────────┐   │   │
    │   │  │ EnsembleRetriever (RRF)      │   │   │
    │   │  │ ├── PGVector (semantic)      │   │   │
    │   │  │ └── PG FTS  (keyword)        │   │   │
    │   │  └──────────────────────────────┘   │   │
    │   └─────────────────────────────────────┘   │
    └─────────────────────────────────────────────┘

Each layer adds value:
- **EnsembleRetriever**: Combines semantic and lexical search via
  Reciprocal Rank Fusion for maximum recall.
- **ContextualCompressionRetriever**: Reranks and filters documents
  using a cross-encoder model (FlashrankRerank) for precision.
- **History-aware retriever**: Reformulates ambiguous queries using
  conversational context before retrieval.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from langchain_classic.chains.history_aware_retriever import (
    create_history_aware_retriever,
)
from langchain_classic.retrievers import (
    ContextualCompressionRetriever,
    EnsembleRetriever,
)
from langchain_community.document_compressors.flashrank_rerank import (
    FlashrankRerank,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_postgres import PGVector

from app.config.settings import Settings, get_settings
from app.infrastructure.ai.pg_fulltext_retriever import PGFullTextSearchRetriever
from app.infrastructure.ai.prompts import QUERY_REFORMULATION_PROMPT

if TYPE_CHECKING:
    from langchain_core.documents import Document
    from sqlalchemy.ext.asyncio import async_sessionmaker

logger = logging.getLogger(__name__)


def _build_metadata_filter(
    user_id: str,
    library_id: UUID,
    shelf_id: UUID | None = None,
) -> dict[str, str]:
    """Build a metadata filter dict for context isolation."""
    meta: dict[str, str] = {
        "user_id": user_id,
        "library_id": str(library_id),
    }
    if shelf_id is not None:
        meta["shelf_id"] = str(shelf_id)
    return meta


def create_ensemble_retriever(
    vector_store: PGVector,
    session_factory: async_sessionmaker,
    user_id: str,
    library_id: UUID,
    shelf_id: UUID | None = None,
    settings: Settings | None = None,
) -> EnsembleRetriever:
    """
    Build an ``EnsembleRetriever`` combining PGVector + PG Full-Text Search.

    Both sub-retrievers are scoped to the same user / library / shelf
    to maintain strict context isolation.

    Args:
        vector_store: LangChain PGVector store instance.
        session_factory: SQLAlchemy async session factory for FTS queries.
        user_id: Current user scope.
        library_id: Library scope.
        shelf_id: Optional shelf scope.
        settings: Configuration overrides.

    Returns:
        ``EnsembleRetriever`` that merges results via Reciprocal Rank Fusion.
    """
    s = settings or get_settings()
    metadata_filter = _build_metadata_filter(user_id, library_id, shelf_id)

    # 1. Semantic retriever (PGVector cosine similarity)
    vector_retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": s.RETRIEVER_VECTOR_TOP_K,
            "filter": metadata_filter,
        },
    )

    # 2. Lexical retriever (PostgreSQL Full-Text Search)
    fts_retriever = PGFullTextSearchRetriever(
        session_factory=session_factory,
        collection_name=s.PGVECTOR_COLLECTION_NAME,
        k=s.RETRIEVER_FTS_TOP_K,
        filter_metadata=metadata_filter,
    )

    # 3. Ensemble with Reciprocal Rank Fusion
    ensemble = EnsembleRetriever(
        retrievers=[vector_retriever, fts_retriever],
        weights=s.RETRIEVER_ENSEMBLE_WEIGHTS,
    )

    logger.info(
        "[Retriever] Built EnsembleRetriever (vector=%d, fts=%d, weights=%s)",
        s.RETRIEVER_VECTOR_TOP_K,
        s.RETRIEVER_FTS_TOP_K,
        s.RETRIEVER_ENSEMBLE_WEIGHTS,
    )
    return ensemble


def create_compression_retriever(
    base_retriever: EnsembleRetriever,
    settings: Settings | None = None,
) -> ContextualCompressionRetriever:
    """
    Wrap a base retriever with FlashrankRerank for contextual compression.

    The reranker re-scores each candidate document against the query using
    a cross-encoder model and returns only the top-n most relevant ones.

    Args:
        base_retriever: The upstream retriever (typically EnsembleRetriever).
        settings: Configuration overrides.

    Returns:
        ``ContextualCompressionRetriever`` with FlashrankRerank compressor.
    """
    s = settings or get_settings()

    compressor = FlashrankRerank(
        top_n=s.RERANKER_TOP_N,
        model="ms-marco-MultiBERT-L-12",
    )

    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever,
    )

    logger.info(
        "[Retriever] Wrapped with FlashrankRerank (top_n=%d)",
        s.RERANKER_TOP_N,
    )
    return compression_retriever


def create_history_aware_retrieval_chain(
    llm: BaseChatModel,
    compression_retriever: ContextualCompressionRetriever,
) -> Runnable[dict, list[Document]]:
    """
    Create a history-aware retriever that reformulates queries.

    When ``chat_history`` is non-empty, the LLM rewrites the user's latest
    question into a standalone query before passing it to the base retriever.
    This handles conversational references like "Tell me more about that"
    or "What about chapter 3?".

    Args:
        llm: LangChain chat model for query reformulation.
        compression_retriever: The full retrieval stack (ensemble + reranker).

    Returns:
        A ``Runnable`` accepting ``{"input": str, "chat_history": list}``
        and returning ``list[Document]``.
    """
    return create_history_aware_retriever(
        llm=llm,
        retriever=compression_retriever,
        prompt=QUERY_REFORMULATION_PROMPT,
    )


def build_full_retrieval_pipeline(
    llm: BaseChatModel,
    vector_store: PGVector,
    session_factory: async_sessionmaker,
    user_id: str,
    library_id: UUID,
    shelf_id: UUID | None = None,
    settings: Settings | None = None,
) -> Runnable[dict, list[Document]]:
    """
    Convenience function — build the complete retrieval pipeline in one call.

    Combines:
    1. EnsembleRetriever (PGVector + PG FTS)
    2. ContextualCompressionRetriever (FlashrankRerank)
    3. History-aware query reformulation

    Args:
        llm: Chat model for query reformulation.
        vector_store: PGVector store.
        session_factory: Async session factory for FTS.
        user_id: User scope.
        library_id: Library scope.
        shelf_id: Optional shelf scope.
        settings: Configuration overrides.

    Returns:
        Ready-to-use ``Runnable`` for document retrieval.
    """
    ensemble = create_ensemble_retriever(
        vector_store, session_factory, user_id, library_id, shelf_id, settings,
    )
    compression = create_compression_retriever(ensemble, settings)
    return create_history_aware_retrieval_chain(llm, compression)
