"""
Concrete SQLAlchemy implementation of IChatRepository.

Handles persistence for chat sessions, messages, and sliding-window summaries.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.chat import ChatMessage, ChatSession, ChatSummary
from app.domain.interfaces.chat_repository import IChatRepository
from app.infrastructure.database.models.chat_model import (
    ChatMessageModel,
    ChatSessionModel,
    ChatSummaryModel,
)


class ChatRepository(IChatRepository):
    """Chat persistence via SQLAlchemy async session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Sessions ─────────────────────────────────────────────────────────────
    @staticmethod
    def _session_to_entity(model: ChatSessionModel) -> ChatSession:
        return ChatSession(
            id=model.id,
            user_id=str(model.user_id),
            library_id=model.library_id,
            shelf_id=model.shelf_id,
            name=model.name,
            created_at=model.created_at,
        )

    async def create_session(self, session: ChatSession) -> ChatSession:
        model = ChatSessionModel(
            id=session.id,
            user_id=session.user_id,
            library_id=session.library_id,
            shelf_id=session.shelf_id,
            created_at=session.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._session_to_entity(model)

    async def get_session(self, session_id: UUID, user_id: str) -> ChatSession | None:
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._session_to_entity(model) if model else None

    async def list_sessions(self, user_id: str, library_id: UUID, shelf_id: UUID | None = None) -> list[ChatSession]:
        """List all chat sessions for a user in a library/shelf."""
        query = select(ChatSessionModel).where(
            ChatSessionModel.user_id == user_id,
            ChatSessionModel.library_id == library_id,
        )
        if shelf_id:
            query = query.where(ChatSessionModel.shelf_id == shelf_id)
        else:
            query = query.where(ChatSessionModel.shelf_id.is_(None))
            
        stmt = query.order_by(ChatSessionModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._session_to_entity(m) for m in result.scalars().all()]

    async def update_session_name(self, session_id: UUID, name: str) -> None:
        from sqlalchemy import update
        stmt = (
            update(ChatSessionModel)
            .where(ChatSessionModel.id == session_id)
            .values(name=name)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def delete_session(self, session_id: UUID, user_id: str) -> None:
        from sqlalchemy import delete
        stmt = delete(ChatSessionModel).where(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == user_id,
        )
        await self._session.execute(stmt)
        await self._session.flush()

    # ── Messages ─────────────────────────────────────────────────────────────
    @staticmethod
    def _message_to_entity(model: ChatMessageModel) -> ChatMessage:
        return ChatMessage(
            id=model.id,
            session_id=model.session_id,
            role=model.role,
            content=model.content,
            from_web=model.from_web,
            token_count=model.token_count,
            references=model.references or [],
            created_at=model.created_at,
        )

    async def add_message(self, message: ChatMessage) -> ChatMessage:
        model = ChatMessageModel(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            from_web=message.from_web,
            token_count=message.token_count,
            references=message.references or None,
            created_at=message.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._message_to_entity(model)

    async def get_messages(
        self, session_id: UUID, limit: int | None = None
    ) -> list[ChatMessage]:
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.session_id == session_id)
            .order_by(ChatMessageModel.created_at.asc())
        )
        if limit is not None:
            # Get the N most recent, but return in chronological order
            sub = (
                select(ChatMessageModel)
                .where(ChatMessageModel.session_id == session_id)
                .order_by(ChatMessageModel.created_at.desc())
                .limit(limit)
            ).subquery()
            stmt = (
                select(ChatMessageModel)
                .join(sub, ChatMessageModel.id == sub.c.id)
                .order_by(ChatMessageModel.created_at.asc())
            )
        result = await self._session.execute(stmt)
        return [self._message_to_entity(m) for m in result.scalars().all()]

    # ── Summaries ────────────────────────────────────────────────────────────
    @staticmethod
    def _summary_to_entity(model: ChatSummaryModel) -> ChatSummary:
        return ChatSummary(
            id=model.id,
            session_id=model.session_id,
            summary_text=model.summary_text,
            summarized_up_to_message_id=model.summarized_up_to_message_id,
            token_count=model.token_count,
            created_at=model.created_at,
        )

    async def save_summary(self, summary: ChatSummary) -> ChatSummary:
        model = ChatSummaryModel(
            id=summary.id,
            session_id=summary.session_id,
            summary_text=summary.summary_text,
            summarized_up_to_message_id=summary.summarized_up_to_message_id,
            token_count=summary.token_count,
            created_at=summary.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._summary_to_entity(model)

    async def get_latest_summary(self, session_id: UUID) -> ChatSummary | None:
        stmt = (
            select(ChatSummaryModel)
            .where(ChatSummaryModel.session_id == session_id)
            .order_by(ChatSummaryModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._summary_to_entity(model) if model else None
