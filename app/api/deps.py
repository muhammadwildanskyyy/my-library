"""
FastAPI dependency injection — wires repositories and services.

Usage in endpoints:
    @router.get("/")
    async def list_items(
        user_id: str = Depends(get_current_user_id),
        library_svc: LibraryService = Depends(get_library_service),
    ): ...
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.config.security import get_current_user_id
from app.infrastructure.ai.embedding_service import EmbeddingService
from app.infrastructure.ai.llm_service import LLMService
from app.infrastructure.ai.rag_pipeline import CorrectiveRAGPipeline
from app.infrastructure.ai.web_search_service import WebSearchService
from app.infrastructure.database.repositories.book_repository import BookRepository
from app.infrastructure.database.repositories.chat_repository import ChatRepository
from app.infrastructure.database.repositories.chunk_repository import ChunkRepository
from app.infrastructure.database.repositories.library_repository import LibraryRepository
from app.infrastructure.database.repositories.shelf_repository import ShelfRepository
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.service.auth_service import AuthService
from app.service.book_service import BookService
from app.service.chat_service import ChatService
from app.service.ingest_book_service import IngestBookService
from app.service.library_service import LibraryService
from app.service.shelf_service import ShelfService


# ---------------------------------------------------------------------------
# Repository factories
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


def get_chunk_repo(
    session: AsyncSession = Depends(get_db_session),
) -> ChunkRepository:
    return ChunkRepository(session)


def get_chat_repo(
    session: AsyncSession = Depends(get_db_session),
) -> ChatRepository:
    return ChatRepository(session)


# ---------------------------------------------------------------------------
# AI Service factories
# ---------------------------------------------------------------------------
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


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
    chunk_repo: ChunkRepository = Depends(get_chunk_repo),
    embedding_svc: EmbeddingService = Depends(get_embedding_service),
) -> IngestBookService:
    return IngestBookService(book_repo, chunk_repo, embedding_svc)


# ---------------------------------------------------------------------------
# AI Service factories (stateful — LLM, web search, RAG pipeline)
# ---------------------------------------------------------------------------
def get_llm_service() -> LLMService:
    return LLMService()


def get_web_search_service() -> WebSearchService:
    return WebSearchService()


def get_rag_pipeline(
    llm_svc: LLMService = Depends(get_llm_service),
    embedding_svc: EmbeddingService = Depends(get_embedding_service),
    chunk_repo: ChunkRepository = Depends(get_chunk_repo),
    web_search_svc: WebSearchService = Depends(get_web_search_service),
) -> CorrectiveRAGPipeline:
    return CorrectiveRAGPipeline(llm_svc, embedding_svc, chunk_repo, web_search_svc)


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
    "get_chunk_repo",
    "get_current_user_id",
    "get_embedding_service",
    "get_ingest_service",
    "get_library_service",
    "get_rag_pipeline",
    "get_shelf_service",
]
