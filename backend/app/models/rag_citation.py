from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RagCitation(Base):
    __tablename__ = "rag_citation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chat_message.id"), nullable=False
    )
    chunk_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    document_title: Mapped[str] = mapped_column(String(200), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
