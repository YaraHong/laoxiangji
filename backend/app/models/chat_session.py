from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.chat_message import ChatMessage


class ChatSession(Base):
    __tablename__ = "chat_session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), default="web", nullable=False)
    visitor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    messages: Mapped[list[ChatMessage]] = relationship(back_populates="session")

    __table_args__ = (
        Index("idx_chat_session_status", "status"),
        Index("idx_chat_session_visitor", "visitor_id"),
    )
