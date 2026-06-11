"""
Library domain entity — the top-level container in the hierarchy.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class Library:
    """
    Top-level knowledge container owned by a single user.
    Hierarchy: Library → Shelf → Book
    Books can also sit directly under a Library (without a shelf).
    """

    id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    name: str = ""
    description: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
