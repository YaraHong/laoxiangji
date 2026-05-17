from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CustomerProfile(Base):
    """客户画像（特征抽取结果）"""

    __tablename__ = "customer_profile"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    budget_range: Mapped[str | None] = mapped_column(String(80), nullable=True)
    has_store: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    store_area: Mapped[float | None] = mapped_column(Float, nullable=True)
    catering_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    open_timeline: Mapped[str | None] = mapped_column(String(80), nullable=True)
    concerns: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    extracted_fields: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    confirmed_fields: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    last_extracted_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
