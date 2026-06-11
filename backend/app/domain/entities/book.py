"""
Book domain entity — an uploaded document in the knowledge hierarchy.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4


@dataclass
class Book:
    """
    A document uploaded to the platform.

    - Always belongs to a Library (library_id is required).
    - Optionally placed on a Shelf (shelf_id is nullable).
    - Can be moved between shelves or back to library root.
    """

    id: UUID = field(default_factory=uuid4)
    library_id: UUID = field(default_factory=uuid4)
    shelf_id: UUID | None = None  # nullable — book can live directly under library
    user_id: str = ""
    title: str = ""
    filename: str = ""
    file_url: str = ""  # URL penyimpanan Cloudinary — wajib ada
    file_size: int = 0
    total_chunks: int = 0
    status: Literal["processing", "completed", "failed"] = "processing"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
