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
    file_url: str
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

class BookUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)



class ChunkItem(BaseModel):
    """A single text chunk extracted from a book."""

    chunk_index: int = Field(..., description="Sequential position of this chunk")
    content: str = Field(..., description="The text content of the chunk")
    source_type: str = Field(..., description="'text' or 'table'")
    page: str = Field(..., description="Page number in the original PDF")
    token_count: str = Field(..., description="Token count of this chunk")


class BookChunksResponse(BaseModel):
    """All chunks for a single book, ordered by chunk_index."""

    chunks: list[ChunkItem]
    total: int
