from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CustomerTag(Base):
    """客户标签"""

    __tablename__ = "customer_tag"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tag_code: Mapped[str] = mapped_column(String(64), nullable=False)
    tag_name: Mapped[str] = mapped_column(String(80), nullable=False)
    source: Mapped[str] = mapped_column(String(24), default="ai", nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_customer_tag_lead", "lead_id"),
        Index("uk_customer_tag", "lead_id", "tag_code", unique=True),
    )
