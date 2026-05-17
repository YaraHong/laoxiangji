import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger_handle import logger
from app.models.customer_lead import CustomerLead
from app.models.customer_profile import CustomerProfile
from app.models.customer_tag import CustomerTag


def _generate_lead_no() -> str:
    """生成线索编号"""
    return f"LEAD{date.today().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"


async def get_lead_by_session(db: AsyncSession, session_id: int) -> CustomerLead | None:
    """通过会话 ID 查找关联线索"""
    result = await db.execute(
        select(CustomerLead).where(CustomerLead.latest_session_id == session_id)
    )
    return result.scalar_one_or_none()


from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession


async def save_or_update_lead(db: AsyncSession, session_id: int, lead_data: dict[str, Any]):
    """
    保存或更新客户线索
    """
    lead = await get_lead_by_session(db, session_id)

    if lead is None:
        new_lead = CustomerLead(
            lead_no=_generate_lead_no(),
            name=lead_data["name"],
            phone=lead_data["phone"],
            wechat=lead_data["wechat"],
            city=lead_data["city"],
            source_channel=None,
            intent_level=lead_data["intent_level"],
            score=lead_data["intent_score"],
            follow_status=None,
            assigned_consultant_id=None,
            latest_session_id=session_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(new_lead)
        lead = new_lead
    else:
        for key, value in lead_data.items():
            if hasattr(lead, key):
                setattr(lead, key, value)

    await db.commit()
    await db.refresh(lead)

    return lead


async def create_lead(db: AsyncSession, *, session_id: int, source_channel: str = "web") -> CustomerLead:
    """创建新线索"""
    lead = CustomerLead(
        lead_no=_generate_lead_no(),
        source_channel=source_channel,
        latest_session_id=session_id,
        intent_level="D",
        score=0,
        follow_status="new",
    )
    db.add(lead)
    await db.flush()
    logger.info("新线索创建: lead_id=%d, lead_no=%s", lead.id, lead.lead_no)
    return lead


async def update_lead(
        db: AsyncSession,
        lead: CustomerLead,
        *,
        name,
        phone,
        wechat,
        city,
        intent_level,
        score,
        session_id,
) -> None:
    """更新线索字段"""
    if name is not None:
        lead.name = name
    if phone is not None:
        lead.phone = phone
    if wechat is not None:
        lead.wechat = wechat
    if city is not None:
        lead.city = city
    if intent_level is not None:
        lead.intent_level = intent_level
    if score is not None:
        lead.score = score
    if session_id is not None:
        lead.latest_session_id = session_id
    lead.updated_at = datetime.now(timezone.utc)
    await db.flush()


async def get_profile_by_lead(db: AsyncSession, lead_id: int) -> CustomerProfile | None:
    """通过线索 ID 查找客户画像"""
    result = await db.execute(
        select(CustomerProfile).where(CustomerProfile.lead_id == lead_id)
    )
    return result.scalar_one_or_none()


async def upsert_profile(db: AsyncSession, lead_id: int, **kwargs) -> CustomerProfile:
    """创建或更新客户画像"""
    profile = await get_profile_by_lead(db, lead_id) or CustomerProfile(lead_id=lead_id)
    if profile.id is None:
        db.add(profile)

    extracted_fields = kwargs.pop('extracted_fields', None)
    if extracted_fields is not None:
        profile.extracted_fields = {**(profile.extracted_fields or {}), **extracted_fields}

    for key, value in kwargs.items():
        if value is not None:
            setattr(profile, key, value)

    profile.updated_at = datetime.now(timezone.utc)
    await db.flush()
    logger.info("客户画像已更新: lead_id=%d", lead_id)
    return profile


async def replace_tags(
        db: AsyncSession,
        lead_id: int,
        tags: list[dict],
) -> None:
    """替换客户标签"""
    await db.execute(
        select(CustomerTag).where(CustomerTag.lead_id == lead_id)
    )
    result = await db.execute(
        select(CustomerTag).where(CustomerTag.lead_id == lead_id)
    )
    existing = result.scalars().all()
    for tag in existing:
        await db.delete(tag)

    for tag_data in tags:
        tag = CustomerTag(
            lead_id=lead_id,
            tag_code=tag_data.get("code", ""),
            tag_name=tag_data.get("name", ""),
            source=tag_data.get("source", "ai"),
            confidence=tag_data.get("confidence"),
        )
        db.add(tag)

    if tags:
        await db.flush()
        logger.info("客户标签已更新: lead_id=%d, count=%d", lead_id, len(tags))
