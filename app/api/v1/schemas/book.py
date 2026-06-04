"""
Pydantic schemas for book endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BookResponse(BaseModel):
    id: UUID
    library_id: UUID
    shelf_id: UUID | None
    user_id: UUID
    title: str
    filename: str
    file_size: int
    total_chunks: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookListResponse(BaseModel):
    books: list[BookResponse]
    total: int


class BookMoveRequest(BaseModel):
    """Move a book to a shelf or back to library root (shelf_id=null)."""

    shelf_id: UUID | None = Field(
        None,
        description="Target shelf ID, or null to move to library root.",
    )
