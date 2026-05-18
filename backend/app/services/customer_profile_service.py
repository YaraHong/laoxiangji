"""客户特征抽取服务"""

from langchain_core.messages import AIMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.core.database import AsyncSessionLocal
from app.core.logger_handle import logger
from app.core.model_factory import chat_llm
from app.crud.customer_profile import (
    upsert_profile, replace_tags, save_or_update_lead,
)
from app.services.prompt_loader import load_prompt
from app.services.redis_cache import get_profile_hint, set_profile_hint

json_output_parser = JsonOutputParser()


async def _log_raw_llm_output(msg: AIMessage) -> AIMessage:
    """打印 LLM 原始输出，便于排查 JSON 解析失败问题"""
    logger.info("LLM 原始输出: %s", msg.content)
    return msg


async def load_profile_for_session(session_id: int) -> dict | None:
    """从 Redis 加载会话的客户特征缓存"""
    return await get_profile_hint(session_id)


def _build_conversation_text(messages: list[dict]) -> str:
    """将消息列表转换为对话文本"""
    lines = []
    for msg in messages:
        role = "用户" if msg.get("role") == "user" else "客服"
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _format_profile_for_prompt(profile: dict | None) -> str:
    """将客户特征格式化为提示词可用的文本"""
    if not profile:
        return "暂无客户特征信息"

    parts = []
    if profile.get("name"):
        parts.append(f"- 姓名: {profile['name']}")
    if profile.get("phone"):
        parts.append(f"- 电话: {profile['phone']}")
    if profile.get("city"):
        parts.append(f"- 城市: {profile['city']}")
    if profile.get("budget_range"):
        parts.append(f"- 预算范围: {profile['budget_range']}")
    if profile.get("has_store") is not None:
        parts.append(f"- 已有店面: {'是' if profile['has_store'] else '否'}")
    if profile.get("store_area"):
        parts.append(f"- 店面面积: {profile['store_area']}㎡")
    if profile.get("catering_experience"):
        parts.append(f"- 餐饮经验: {profile['catering_experience']}")
    if profile.get("open_timeline"):
        parts.append(f"- 开店时间规划: {profile['open_timeline']}")
    if profile.get("concerns"):
        parts.append(f"- 关注点: {', '.join(profile['concerns'])}")
    if profile.get("intent_level"):
        level_map = {"S": "已决定加盟", "A": "强烈意向", "B": "中等意向", "C": "低意向", "D": "初步了解"}
        parts.append(f"- 意向等级: {level_map.get(profile['intent_level'], profile['intent_level'])}")

    tags = profile.get("tags", [])
    if tags:
        tag_names = [t.get("name", t.get("code", "")) for t in tags]
        parts.append(f"- 客户标签: {', '.join(tag_names)}")

    return "\n".join(parts) if parts else "暂无客户特征信息"


def _build_profile_summary(extracted: dict) -> dict:
    """将 LLM 提取结果转换为 Redis 缓存的 profile 摘要"""
    return {
        "name": extracted.get("name"),
        "phone": extracted.get("phone"),
        "wechat": extracted.get("wechat"),
        "city": extracted.get("city"),
        "budget_range": extracted.get("budget_range"),
        "has_store": extracted.get("has_store"),
        "store_area": extracted.get("store_area"),
        "catering_experience": extracted.get("catering_experience"),
        "open_timeline": extracted.get("open_timeline"),
        "concerns": extracted.get("concerns", []),
        "intent_level": extracted.get("intent_level", "D"),
        "intent_score": extracted.get("intent_score", 0),
        "tags": extracted.get("tags", []),
        "need_followup": extracted.get("need_followup", False),
        "followup_questions": extracted.get("followup_questions", []),
    }


async def trait_extraction(
        session_id: int,
        messages: list[dict],
) -> dict | None:
    """
    从对话中抽取客户特征
    """

    logger.info("开始抽取客户特征")

    if not messages:
        return None

    async with AsyncSessionLocal() as db:
        try:
            # 调用大模型抽取客户特征
            prompt = load_prompt("trait_extraction.txt")
            conversation = _build_conversation_text(messages)
            template = PromptTemplate.from_template(prompt)
            chain = template | chat_llm | json_output_parser

            result_json = await chain.ainvoke(input={"conversation": conversation})

            if result_json is None:
                logger.warning("客户特征抽取失败（result_json 为 None），跳过本轮特征更新")
                return None

            # 持久化到数据库：查找或创建线索
            lead = await save_or_update_lead(db, session_id, result_json)

            # 更新客户画像
            await upsert_profile(
                db,
                lead.id,
                budget_range=result_json.get("budget_range"),
                has_store=result_json.get("has_store"),
                store_area=result_json.get("store_area"),
                catering_experience=result_json.get("catering_experience"),
                open_timeline=result_json.get("open_timeline"),
                concerns=result_json.get("concerns"),
                extracted_fields=result_json,
            )

            # 更新标签
            tags = result_json.get("tags", [])

            if tags:
                await replace_tags(db, lead.id, tags)

            await db.commit()

            logger.info("客户特征已持久化: session_id=%d, lead_id=%d", session_id, lead.id)

            await set_profile_hint(session_id, result_json)

            return None
        except Exception:
            logger.exception("客户特征抽取失败: session_id=%d", session_id)
            await db.rollback()
            return None
