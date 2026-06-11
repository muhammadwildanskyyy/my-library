"""
User domain entity — pure dataclass, no external framework dependencies.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class User:
    """Registered user of the AI Librarian platform."""

    id: UUID = field(default_factory=uuid4)
    email: str = ""
    username: str = ""
    hashed_password: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
