from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ChatMessage(Base):
    __tablename__ = "chat_message"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chat_session.id"), nullable=False)
    role: Mapped[str] = mapped_column("role", String(24), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(24), default="text", nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    message_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped[ChatSession] = relationship(back_populates="messages")

    __table_args__ = (
        Index("idx_chat_message_role", "role"),
        Index("idx_chat_message_session", "session_id", "id"),
    )
