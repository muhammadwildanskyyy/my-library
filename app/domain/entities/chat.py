"""
Chat domain entities — session, message, and summary for sliding-window memory.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4


@dataclass
class ChatSession:
    """A conversation session scoped to a user and a library/shelf context."""

    id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    library_id: UUID = field(default_factory=uuid4)
    shelf_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ChatMessage:
    """A single message within a chat session."""

    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(default_factory=uuid4)
    role: Literal["user", "assistant", "system"] = "user"
    content: str = ""
    from_web: bool = False
    token_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ChatSummary:
    """
    Compressed summary of older messages in a session.

    Used by the sliding-window memory strategy to keep context
    within LLM token limits while preserving conversational continuity.
    """

    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(default_factory=uuid4)
    summary_text: str = ""
    summarized_up_to_message_id: UUID = field(default_factory=uuid4)
    token_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
