"""
Chat service — orchestrates the Corrective RAG pipeline with sliding-window memory.

Flow for each user message:
  1. Load or create chat session
  2. Build conversation context (summary + recent messages)
  3. Run Corrective RAG pipeline
  4. Persist user message + assistant response
  5. Check if memory compression is needed → summarize if so

Memory strategy:
  - Keep recent messages within SLIDING_WINDOW_TOKEN_LIMIT
  - When exceeded, LLM summarizes older messages into a ChatSummary
  - New conversations start with the summary as context
"""

import logging
from uuid import UUID

import tiktoken

from app.config.settings import Settings, get_settings
from app.domain.entities.chat import ChatMessage, ChatSession, ChatSummary
from app.domain.interfaces.ai_service import ILLMService
from app.domain.interfaces.chat_repository import IChatRepository
from app.infrastructure.ai.rag_pipeline import CorrectiveRAGPipeline

logger = logging.getLogger(__name__)


class ChatSessionNotFoundError(Exception):
    """Raised when a chat session is not found or not owned by the user."""


class ChatService:
    """
    Orchestrate conversational RAG with persistent memory.

    Each chat session is scoped to a user + library (+ optional shelf),
    matching the same hierarchy used for pre-filtering in the RAG pipeline.
    """

    def __init__(
        self,
        chat_repo: IChatRepository,
        llm_service: ILLMService,
        rag_pipeline: CorrectiveRAGPipeline,
        settings: Settings | None = None,
    ) -> None:
        self._chat_repo = chat_repo
        self._llm = llm_service
        self._rag = rag_pipeline

        s = settings or get_settings()
        self._token_limit = s.SLIDING_WINDOW_TOKEN_LIMIT
        self._summarize_count = s.SLIDING_WINDOW_SUMMARIZE_COUNT
        self._encoder = tiktoken.get_encoding("cl100k_base")

    # ── Public API ───────────────────────────────────────────────────────────
    async def create_session(
        self,
        user_id: str,
        library_id: UUID,
        shelf_id: UUID | None = None,
    ) -> ChatSession:
        """Create a new chat session scoped to a library/shelf."""
        session = ChatSession(
            user_id=user_id,
            library_id=library_id,
            shelf_id=shelf_id,
        )
        return await self._chat_repo.create_session(session)

    async def get_session(
        self, session_id: UUID, user_id: str
    ) -> ChatSession:
        """Get a chat session, ensuring ownership."""
        session = await self._chat_repo.get_session(session_id, user_id)
        if not session:
            raise ChatSessionNotFoundError(
                f"Chat session '{session_id}' not found or access denied."
            )
        return session

    async def list_sessions(
        self, user_id: str, library_id: UUID, shelf_id: UUID | None = None
    ) -> list[ChatSession]:
        """List all chat sessions for a user in a library/shelf."""
        return await self._chat_repo.list_sessions(user_id, library_id, shelf_id)

    async def update_session(self, session_id: UUID, user_id: str, name: str) -> ChatSession:
        """Update session name."""
        session = await self.get_session(session_id, user_id)
        await self._chat_repo.update_session_name(session_id, name)
        session.name = name
        return session

    async def delete_session(self, session_id: UUID, user_id: str) -> None:
        """Delete a chat session."""
        await self.get_session(session_id, user_id)
        await self._chat_repo.delete_session(session_id, user_id)

    async def get_history(
        self, session_id: UUID, user_id: str
    ) -> list[ChatMessage]:
        """Get full message history for a session."""
        # Verify ownership
        await self.get_session(session_id, user_id)
        return await self._chat_repo.get_messages(session_id)

    async def chat(
        self,
        session_id: UUID,
        user_id: str,
        question: str,
    ) -> dict:
        """
        Process a user message through the Corrective RAG pipeline.

        Returns:
            Dict with 'answer', 'used_web', 'session_id', 'from_web',
            'num_docs_retrieved', 'num_docs_relevant'.
        """
        # 1. Verify session ownership and get context
        session = await self.get_session(session_id, user_id)

        # 2. Build conversation context as message history
        chat_history = await self._build_chat_history(session_id)

        # 3. Persist user message
        user_token_count = len(self._encoder.encode(question))
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=question,
            token_count=user_token_count,
        )
        await self._chat_repo.add_message(user_msg)

        # 4. Run Corrective RAG pipeline
        rag_result = await self._rag.run(
            question=question,
            user_id=user_id,
            library_id=session.library_id,
            shelf_id=session.shelf_id,
            chat_history=chat_history,
        )

        answer = rag_result["answer"]
        used_web = rag_result["used_web"]

        # 5. Persist assistant response
        assistant_token_count = len(self._encoder.encode(answer))
        references = rag_result.get("references", [])
        # Serialize references to plain dicts for JSONB storage
        refs_as_dicts = [
            ref if isinstance(ref, dict) else ref.__dict__
            for ref in references
        ]
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=answer,
            from_web=used_web,
            token_count=assistant_token_count,
            references=refs_as_dicts,
        )
        await self._chat_repo.add_message(assistant_msg)

        # 6. Generate title if not exists
        if not session.name:
            try:
                new_title = await self._llm.generate_session_title(question, answer)
                await self._chat_repo.update_session_name(session_id, new_title)
            except Exception as e:
                logger.error(f"Failed to generate title for session {session_id}: {e}")

        # 7. Check if we need to compress memory
        await self._maybe_summarize(session_id)

        return {
            "answer": answer,
            "used_web": used_web,
            "session_id": str(session_id),
            "message_id": str(assistant_msg.id),
            "num_docs_retrieved": rag_result.get("num_docs_retrieved", 0),
            "num_docs_relevant": rag_result.get("num_docs_relevant", 0),
            "references": rag_result.get("references", []),
        }

    # ── Memory Management ────────────────────────────────────────────────────
    async def _build_chat_history(self, session_id: UUID) -> list[dict]:
        """
        Build conversation history as a list of role/content dicts.

        The RAG pipeline uses these dicts for:
        - History-aware query reformulation (via ``create_history_aware_retriever``)
        - Generation prompt context (via ``MessagesPlaceholder``)

        Returns:
            List of dicts with ``role`` and ``content`` keys.
        """
        history: list[dict] = []

        # Include latest summary as a system-level context message
        summary = await self._chat_repo.get_latest_summary(session_id)
        if summary:
            history.append(
                {
                    "role": "assistant",
                    "content": f"[Previous conversation summary]: {summary.summary_text}",
                }
            )

        # Get recent messages
        messages = await self._chat_repo.get_messages(session_id)

        # If we have a summary, only include messages after the summarized point
        if summary and messages:
            after_summary = []
            found = False
            for msg in messages:
                if found:
                    after_summary.append(msg)
                if msg.id == summary.summarized_up_to_message_id:
                    found = True
            if not after_summary and messages:
                after_summary = messages[-self._summarize_count:]
            messages = after_summary

        # Convert to role/content dicts
        for msg in messages:
            history.append({"role": msg.role, "content": msg.content})

        return history

    async def _maybe_summarize(self, session_id: UUID) -> None:
        """
        Check if the conversation needs memory compression.

        Triggers summarization when the total token count of recent
        messages exceeds SLIDING_WINDOW_TOKEN_LIMIT.
        """
        messages = await self._chat_repo.get_messages(session_id)
        if len(messages) < self._summarize_count:
            return

        # Calculate total tokens of recent messages
        total_tokens = sum(m.token_count for m in messages)
        if total_tokens <= self._token_limit:
            return

        logger.info(
            f"[Memory] Session {session_id}: {total_tokens} tokens > "
            f"{self._token_limit} limit — compressing"
        )

        # Take the older half of messages to summarize
        cutoff = len(messages) // 2
        to_summarize = messages[:cutoff]

        if not to_summarize:
            return

        # Build messages for summarization
        summary_input = [
            {"role": m.role, "content": m.content}
            for m in to_summarize
        ]

        # Generate summary using LLM
        summary_text = await self._llm.summarize(summary_input)
        summary_tokens = len(self._encoder.encode(summary_text))

        # Persist summary
        summary = ChatSummary(
            session_id=session_id,
            summary_text=summary_text,
            summarized_up_to_message_id=to_summarize[-1].id,
            token_count=summary_tokens,
        )
        await self._chat_repo.save_summary(summary)

        logger.info(
            f"[Memory] Summarized {len(to_summarize)} messages → "
            f"{summary_tokens} tokens"
        )
