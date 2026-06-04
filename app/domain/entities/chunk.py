"""
Chunk domain entity — an embedded segment of a Book stored in pgvector.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class Chunk:
    """
    A text chunk from a processed Book, stored with its vector embedding.

    Metadata fields (user_id, library_id, shelf_id, book_id) enable
    strict hierarchical pre-filtering before similarity search.
    """

    id: UUID = field(default_factory=uuid4)
    book_id: UUID = field(default_factory=uuid4)
    library_id: UUID = field(default_factory=uuid4)
    shelf_id: UUID | None = None
    user_id: str = ""
    content: str = ""
    chunk_index: int = 0
    token_count: int = 0
    embedding: list[float] = field(default_factory=list)
    source_type: str = "text"  # "text" | "table"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
