"""
Pydantic schemas for library endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LibraryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None

class LibraryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None



class LibraryResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LibraryListResponse(BaseModel):
    libraries: list[LibraryResponse]
    total: int
