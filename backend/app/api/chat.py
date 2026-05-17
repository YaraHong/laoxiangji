from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.core.database import get_db
from app.core.response import success
from app.schemas.chat import (
    CreateMessageRequest,
    CreateSessionRequest,
    MessageResponse,
    SessionInfo,
)
from app.services.chat_service import (
    create_session,
    get_cached_messages,
    get_session_with_messages,
)
from app.services.customer_service.workflow import run_customer_pipeline

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _build_message_response(msg) -> MessageResponse:
    meta = msg.message_metadata or {}
    return MessageResponse(
        id=msg.id,
        session_id=msg.session_id,
        role=msg.role,
        content=msg.content,
        message_type=msg.message_type,
        confidence=float(msg.confidence) if msg.confidence is not None else None,
        citations=meta.get("citations", []),
        created_at=msg.created_at,
    )


def _build_message_response_from_cache(data: dict) -> MessageResponse:
    return MessageResponse(
        id=data["id"],
        session_id=data.get("session_id", 0),
        role=data["role"],
        content=data["content"],
        message_type=data.get("message_type", "text"),
        citations=data.get("citations", []),
        created_at=data["created_at"],
    )


@router.post("/sessions")
async def create_chat_session(
        request: CreateSessionRequest,
        db: AsyncSession = Depends(get_db),
):
    session = await create_session(
        db, channel=request.channel, visitor_id=request.visitor_id
    )
    return success({"session_id": session.id, "session_no": session.session_no})


@router.get("/sessions/{session_id}")
async def get_chat_session(
        session_id: int,
        db: AsyncSession = Depends(get_db),
):
    session = await get_session_with_messages(db, session_id)
    cached = await get_cached_messages(db, session_id)
    messages = [_build_message_response_from_cache(m) for m in cached]
    return success(
        {
            "session": SessionInfo.model_validate(session).model_dump(),
            "messages": [m.model_dump() if hasattr(m, 'model_dump') else m for m in messages],
        }
    )


@router.post("/sessions/{session_id}/messages/stream")
async def stream_chat_message(
        session_id: int,
        request: CreateMessageRequest,
        db: AsyncSession = Depends(get_db),
):
    return StreamingResponse(
        run_customer_pipeline(
            db,
            session_id,
            request.content
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
