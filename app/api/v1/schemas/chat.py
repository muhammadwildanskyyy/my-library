"""
Pydantic schemas for chat endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------
class ChatSessionCreate(BaseModel):
    library_id: UUID = Field(..., description="Library to scope this chat to")
    shelf_id: UUID | None = Field(
        None, description="Optional shelf to narrow the context"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "library_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "shelf_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                }
            ]
        }
    }


class ChatSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    library_id: UUID
    shelf_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionListResponse(BaseModel):
    sessions: list[ChatSessionResponse]
    total: int


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    question: str = Field(
        ..., min_length=1, max_length=10000, description="User's question"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "Jelaskan apa itu AGI dan tantangan utamanya?"
                }
            ]
        }
    }


class ReferenceItem(BaseModel):
    """A citation reference linking generated text to a source document."""

    ref_index: int = Field(..., description="Reference number (1, 2, 3...)")
    book_id: UUID = Field(..., description="Source book ID")
    book_title: str = Field(..., description="Title of the source book")
    filename: str = Field(..., description="Original PDF filename")
    chunk_index: int = Field(..., description="Chunk position within the book")
    source_type: str = Field(..., description="Content type: 'text' or 'table'")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ref_index": 1,
                    "book_id": "810ba871-b6cf-4777-81f5-42548d2c6295",
                    "book_title": "Level AGI",
                    "filename": "level-agi.pdf",
                    "chunk_index": 0,
                    "source_type": "text",
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    answer: str
    used_web: bool = Field(
        ..., description="Whether web search was used as fallback"
    )
    session_id: UUID
    message_id: UUID
    num_docs_retrieved: int
    num_docs_relevant: int
    references: list[ReferenceItem] = Field(
        default_factory=list,
        description="Citation references linking answer to source documents",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "answer": (
                        "AGI (Artificial General Intelligence) adalah bentuk "
                        "kecerdasan buatan teoretis yang memiliki kemampuan untuk "
                        "memahami, belajar, dan menerapkan kecerdasan pada berbagai "
                        "masalah [1]. Karakteristik utama AGI meliputi penalaran "
                        "logis, pengetahuan umum, dan kreativitas asli [1]. "
                        "Saat ini, industri sedang membangun pondasi menuju AGI "
                        "melalui agen otonom dan sistem multimodal [2]."
                    ),
                    "used_web": False,
                    "session_id": "d4e5f6a7-b8c9-0123-def4-567890abcdef",
                    "message_id": "e5f6a7b8-c9d0-1234-ef56-7890abcdef01",
                    "num_docs_retrieved": 5,
                    "num_docs_relevant": 3,
                    "references": [
                        {
                            "ref_index": 1,
                            "book_id": "810ba871-b6cf-4777-81f5-42548d2c6295",
                            "book_title": "Level AGI",
                            "filename": "level-agi.pdf",
                            "chunk_index": 0,
                            "source_type": "text",
                        },
                        {
                            "ref_index": 2,
                            "book_id": "810ba871-b6cf-4777-81f5-42548d2c6295",
                            "book_title": "Level AGI",
                            "filename": "level-agi.pdf",
                            "chunk_index": 3,
                            "source_type": "text",
                        },
                    ],
                }
            ]
        }
    }


class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    from_web: bool
    token_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
    total: int

