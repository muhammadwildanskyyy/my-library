"""
Shelf domain entity — optional organizational layer within a Library.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class Shelf:
    """
    Organizational group within a Library.
    Books can be placed on a shelf for finer context isolation.
    """

    id: UUID = field(default_factory=uuid4)
    library_id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    name: str = ""
    description: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
