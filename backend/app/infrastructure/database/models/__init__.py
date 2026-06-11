"""
SQLAlchemy ORM models — import all models here so Alembic can discover them.
"""

from app.infrastructure.database.models.book_model import BookModel
from app.infrastructure.database.models.chat_model import (
    ChatMessageModel,
    ChatSessionModel,
    ChatSummaryModel,
)
from app.infrastructure.database.models.library_model import LibraryModel
from app.infrastructure.database.models.shelf_model import ShelfModel
from app.infrastructure.database.models.user_model import UserModel

__all__ = [
    "BookModel",
    "ChatMessageModel",
    "ChatSessionModel",
    "ChatSummaryModel",
    "LibraryModel",
    "ShelfModel",
    "UserModel",
]
