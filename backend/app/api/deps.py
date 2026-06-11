"""
FastAPI dependency injection — wires repositories and services.

Usage in endpoints::

    @router.get("/")
    async def list_items(
        user_id: str = Depends(get_current_user_id),
        library_svc: LibraryService = Depends(get_library_service),
    ): ...

Architecture note:
- **CRUD** layer uses SQLAlchemy async sessions (``asyncpg``).
- **AI/RAG** layer uses ``langchain_postgres.PGVector`` (``psycopg3``)
  and the ``EnsembleRetriever`` + ``ContextualCompressionRetriever`` stack.
"""

from functools import lru_cache
from fastapi import Depends
from langchain_core.language_models import BaseChatModel
from langchain_postgres import PGVector
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import async_session_factory, get_db_session
from app.config.security import get_current_user_id
from app.infrastructure.ai.embedding_service import EmbeddingService
from app.infrastructure.ai.llm_factory import create_chat_model
from app.infrastructure.ai.llm_service import LLMService
from app.infrastructure.ai.rag_pipeline import CorrectiveRAGPipeline
from app.infrastructure.ai.web_search_service import WebSearchService
from app.infrastructure.database.pgvector_store import create_pgvector_store
from app.infrastructure.database.repositories.book_repository import BookRepository
from app.infrastructure.database.repositories.chat_repository import ChatRepository
from app.infrastructure.database.repositories.library_repository import LibraryRepository
from app.infrastructure.database.repositories.shelf_repository import ShelfRepository
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.ingestion.langchain_chunker import LangChainChunker
from app.service.auth_service import AuthService
from app.service.book_service import BookService
from app.service.chat_service import ChatService
from app.service.ingest_book_service import IngestBookService
from app.service.library_service import LibraryService
from app.service.shelf_service import ShelfService


# ---------------------------------------------------------------------------
# Repository factories (SQLAlchemy CRUD — unchanged)
# ---------------------------------------------------------------------------
def get_user_repo(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session)


def get_library_repo(
    session: AsyncSession = Depends(get_db_session),
) -> LibraryRepository:
    return LibraryRepository(session)


def get_shelf_repo(
    session: AsyncSession = Depends(get_db_session),
) -> ShelfRepository:
    return ShelfRepository(session)


def get_book_repo(
    session: AsyncSession = Depends(get_db_session),
) -> BookRepository:
    return BookRepository(session)


def get_chat_repo(
    session: AsyncSession = Depends(get_db_session),
) -> ChatRepository:
    return ChatRepository(session)


# ---------------------------------------------------------------------------
# AI Service factories
# ---------------------------------------------------------------------------
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


def get_chat_model() -> BaseChatModel:
    """Raw LangChain chat model — used by RAG pipeline and retriever chain."""
    return create_chat_model()


def get_pgvector_store(
    embedding_svc: EmbeddingService = Depends(get_embedding_service),
) -> PGVector:
    """LangChain PGVector store for document storage and semantic retrieval."""
    return create_pgvector_store(embedding_svc._embedder)


def get_langchain_chunker() -> LangChainChunker:
    """Chunker using langchain_text_splitters for document splitting."""
    return LangChainChunker()


# ---------------------------------------------------------------------------
# Service factories
# ---------------------------------------------------------------------------
def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
) -> AuthService:
    return AuthService(user_repo)


def get_library_service(
    library_repo: LibraryRepository = Depends(get_library_repo),
) -> LibraryService:
    return LibraryService(library_repo)


def get_shelf_service(
    shelf_repo: ShelfRepository = Depends(get_shelf_repo),
    library_repo: LibraryRepository = Depends(get_library_repo),
) -> ShelfService:
    return ShelfService(shelf_repo, library_repo)


def get_book_service(
    book_repo: BookRepository = Depends(get_book_repo),
    library_repo: LibraryRepository = Depends(get_library_repo),
    shelf_repo: ShelfRepository = Depends(get_shelf_repo),
) -> BookService:
    return BookService(book_repo, library_repo, shelf_repo)


def get_ingest_service(
    book_repo: BookRepository = Depends(get_book_repo),
    vector_store: PGVector = Depends(get_pgvector_store),
    chunker: LangChainChunker = Depends(get_langchain_chunker),
    session: AsyncSession = Depends(get_db_session),
) -> IngestBookService:
    """Ingestion service using LangChain chunker + PGVector store."""
    return IngestBookService(
        book_repo=book_repo,
        vector_store=vector_store,
        chunker=chunker,
        db_session=session,
    )


from app.infrastructure.storage.cloudinary_service import CloudinaryService

# ---------------------------------------------------------------------------
# AI Service factories (RAG pipeline)
# ---------------------------------------------------------------------------
def get_llm_service() -> LLMService:
    return LLMService()

@lru_cache
def get_cloudinary_service() -> CloudinaryService:
    return CloudinaryService()


@lru_cache
def get_web_search_service() -> WebSearchService:
    return WebSearchService()


def get_rag_pipeline(
    llm: BaseChatModel = Depends(get_chat_model),
    vector_store: PGVector = Depends(get_pgvector_store),
    web_search_svc: WebSearchService = Depends(get_web_search_service),
) -> CorrectiveRAGPipeline:
    """
    Build the Corrective RAG pipeline with hybrid retrieval.

    The pipeline creates scoped retrievers per-request using the
    ``async_session_factory`` and user/library/shelf context.
    """
    return CorrectiveRAGPipeline(
        llm=llm,
        vector_store=vector_store,
        session_factory=async_session_factory,
        web_search_service=web_search_svc,
    )


def get_chat_service(
    chat_repo: ChatRepository = Depends(get_chat_repo),
    llm_svc: LLMService = Depends(get_llm_service),
    rag_pipeline: CorrectiveRAGPipeline = Depends(get_rag_pipeline),
) -> ChatService:
    return ChatService(chat_repo, llm_svc, rag_pipeline)


# Re-export for convenience
__all__ = [
    "get_auth_service",
    "get_book_service",
    "get_chat_service",
    "get_chat_model",
    "get_current_user_id",
    "get_embedding_service",
    "get_ingest_service",
    "get_langchain_chunker",
    "get_library_service",
    "get_pgvector_store",
    "get_rag_pipeline",
    "get_shelf_service",
]
