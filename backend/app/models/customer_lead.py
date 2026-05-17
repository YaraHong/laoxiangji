from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CustomerLead(Base):
    """客户线索"""

    __tablename__ = "customer_lead"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    wechat: Mapped[str | None] = mapped_column(String(80), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_channel: Mapped[str] = mapped_column(String(32), default="web", nullable=False)
    intent_level: Mapped[str] = mapped_column(String(8), default="D", nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    follow_status: Mapped[str] = mapped_column(String(32), default="new", nullable=False)
    assigned_consultant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    latest_session_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_customer_lead_level", "intent_level"),
        Index("idx_customer_lead_city", "city"),
        Index("idx_customer_lead_phone", "phone"),
    )
