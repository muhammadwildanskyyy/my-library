"""
Abstract interface for the Chat repository.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.chat import ChatMessage, ChatSession, ChatSummary


class IChatRepository(ABC):
    """Contract for chat session, message, and summary persistence."""

    # --- Sessions -----------------------------------------------------------
    @abstractmethod
    async def create_session(self, session: ChatSession) -> ChatSession:
        """Create a new chat session."""
        ...

    @abstractmethod
    async def get_session(self, session_id: UUID, user_id: str) -> ChatSession | None:
        """Find a chat session by ID, scoped to user."""
        ...

    @abstractmethod
    async def update_session_name(self, session_id: UUID, name: str) -> None:
        """Update the name of a chat session."""
        ...

    @abstractmethod
    async def list_sessions(self, user_id: str, library_id: UUID, shelf_id: UUID | None = None) -> list[ChatSession]:
        """List all chat sessions for a user in a library/shelf."""
        ...

    @abstractmethod
    async def delete_session(self, session_id: UUID, user_id: str) -> None:
        """Delete a chat session by ID."""
        ...

    # --- Messages -----------------------------------------------------------
    @abstractmethod
    async def add_message(self, message: ChatMessage) -> ChatMessage:
        """Persist a new chat message."""
        ...

    @abstractmethod
    async def get_messages(
        self, session_id: UUID, limit: int | None = None
    ) -> list[ChatMessage]:
        """
        Get messages for a session, ordered by created_at ascending.
        If limit is set, returns the N most recent messages.
        """
        ...

    # --- Summaries ----------------------------------------------------------
    @abstractmethod
    async def save_summary(self, summary: ChatSummary) -> ChatSummary:
        """Persist a chat summary (sliding-window compression)."""
        ...

    @abstractmethod
    async def get_latest_summary(self, session_id: UUID) -> ChatSummary | None:
        """Get the most recent summary for a session, or None."""
        ...
