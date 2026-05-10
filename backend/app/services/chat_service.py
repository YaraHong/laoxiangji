import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.logger_handle import logger
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.services.redis_cache import get_messages, push_message


def _generate_session_no() -> str:
    return f"LXJ{date.today().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"


async def create_session(
        db: AsyncSession, *, channel: str = "web", visitor_id: str | None = None
) -> ChatSession:
    session = ChatSession(
        session_no=_generate_session_no(),
        channel=channel,
        visitor_id=visitor_id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info("会话创建: id=%d, no=%s, channel=%s", session.id, session.session_no, channel)
    return session


async def get_session_with_messages(db: AsyncSession, session_id: int) -> ChatSession:
    stmt = (
        select(ChatSession)
        .options(joinedload(ChatSession.messages))
        .where(ChatSession.id == session_id)
    )
    result = await db.execute(stmt)
    session = result.unique().scalar_one_or_none()
    if session is None:
        logger.warning("会话不存在: id=%d", session_id)
        raise HTTPException(status_code=404, detail="会话不存在")
    if session.messages:
        session.messages.sort(key=lambda m: m.created_at)
    return session


async def save_user_message(db: AsyncSession, session_id: int, content: str) -> ChatMessage:
    msg = ChatMessage(session_id=session_id, role="user", content=content)
    db.add(msg)
    await db.flush()

    stmt = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one()
    session.last_message_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(msg)
    await push_message(session_id, msg)
    return msg


async def save_assistant_message(
        db: AsyncSession,
        session_id: int,
        content: str,
        message_type: str = "text",
        citations: list[dict] | None = None,
        lead_hint: dict | None = None,
) -> ChatMessage:
    meta: dict = {}
    if citations:
        meta["citations"] = citations
    if lead_hint:
        meta["lead_hint"] = lead_hint

    msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=content,
        message_type=message_type,
        message_metadata=meta,
    )
    db.add(msg)
    await db.flush()

    stmt = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one()
    session.last_message_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(msg)
    await push_message(session_id, msg)
    return msg


async def get_cached_messages(db: AsyncSession, session_id: int) -> list[dict]:
    cached = await get_messages(session_id)
    if cached:
        return cached

    session = await get_session_with_messages(db, session_id)
    recent = session.messages[-20:] if len(session.messages) > 20 else session.messages
    for msg in recent:
        await push_message(session_id, msg)
    return [
        {
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "content": m.content,
            "message_type": m.message_type,
            "citations": (m.message_metadata or {}).get("citations", []),
            "created_at": m.created_at.isoformat()
        }
        for m in session.messages
    ]
