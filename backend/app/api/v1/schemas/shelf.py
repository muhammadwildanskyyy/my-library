"""
Pydantic schemas for shelf endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ShelfCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None

class ShelfUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None



class ShelfResponse(BaseModel):
    id: UUID
    library_id: UUID
    user_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShelfListResponse(BaseModel):
    shelves: list[ShelfResponse]
    total: int
