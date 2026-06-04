"""
Chat endpoints — sessions, messaging, and history.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_chat_service, get_current_user_id
from app.api.v1.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionCreate,
    ChatSessionListResponse,
    ChatSessionResponse,
    ReferenceItem,
)
from app.service.chat_service import ChatService, ChatSessionNotFoundError

router = APIRouter(prefix="/chat", tags=["Chat"])


# ---------------------------------------------------------------------------
# Create a new chat session
# ---------------------------------------------------------------------------
@router.post(
    "/sessions/",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session scoped to a library/shelf",
)
async def create_session(
    body: ChatSessionCreate,
    user_id: str = Depends(get_current_user_id),
    chat_svc: ChatService = Depends(get_chat_service),
) -> ChatSessionResponse:
    session = await chat_svc.create_session(
        user_id=user_id,
        library_id=body.library_id,
        shelf_id=body.shelf_id,
    )
    return ChatSessionResponse(
        id=session.id,
        user_id=UUID(session.user_id),
        library_id=session.library_id,
        shelf_id=session.shelf_id,
        created_at=session.created_at,
    )


# ---------------------------------------------------------------------------
# List chat sessions for a library
# ---------------------------------------------------------------------------
@router.get(
    "/sessions/",
    response_model=ChatSessionListResponse,
    summary="List chat sessions for a library",
)
async def list_sessions(
    library_id: UUID,
    user_id: str = Depends(get_current_user_id),
    chat_svc: ChatService = Depends(get_chat_service),
) -> ChatSessionListResponse:
    sessions = await chat_svc.list_sessions(user_id, library_id)
    return ChatSessionListResponse(
        sessions=[
            ChatSessionResponse(
                id=s.id,
                user_id=UUID(s.user_id),
                library_id=s.library_id,
                shelf_id=s.shelf_id,
                created_at=s.created_at,
            )
            for s in sessions
        ],
        total=len(sessions),
    )


# ---------------------------------------------------------------------------
# Send a message (trigger Corrective RAG pipeline)
# ---------------------------------------------------------------------------
@router.post(
    "/sessions/{session_id}/messages/",
    response_model=ChatResponse,
    summary="Send a message — triggers the Corrective RAG pipeline",
)
async def send_message(
    session_id: UUID,
    body: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    chat_svc: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    try:
        result = await chat_svc.chat(
            session_id=session_id,
            user_id=user_id,
            question=body.question,
        )
    except ChatSessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return ChatResponse(
        answer=result["answer"],
        used_web=result["used_web"],
        session_id=UUID(result["session_id"]),
        message_id=UUID(result["message_id"]),
        num_docs_retrieved=result["num_docs_retrieved"],
        num_docs_relevant=result["num_docs_relevant"],
        references=[
            ReferenceItem(**ref) for ref in result.get("references", [])
        ],
    )


# ---------------------------------------------------------------------------
# Get chat history
# ---------------------------------------------------------------------------
@router.get(
    "/sessions/{session_id}/messages/",
    response_model=ChatHistoryResponse,
    summary="Get message history for a chat session",
)
async def get_history(
    session_id: UUID,
    user_id: str = Depends(get_current_user_id),
    chat_svc: ChatService = Depends(get_chat_service),
) -> ChatHistoryResponse:
    try:
        messages = await chat_svc.get_history(session_id, user_id)
    except ChatSessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return ChatHistoryResponse(
        messages=[
            ChatMessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                from_web=m.from_web,
                token_count=m.token_count,
                created_at=m.created_at,
            )
            for m in messages
        ],
        total=len(messages),
    )
