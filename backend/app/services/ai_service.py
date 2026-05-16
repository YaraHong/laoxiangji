import json
import re
from string import Template
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.logger_handle import logger


def _parse_json_response(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return {
        "content": text,
        "citations": [],
        "lead_hint": {"should_ask": False, "message": "", "suggested_questions": []},
    }


def build_messages(history: list[dict] | None, system_prompt: str, user_message: str) -> list:
    messages = [SystemMessage(content=system_prompt)]
    if history:
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=user_message))
    return messages


def _summarize_history(history: list[dict] | None) -> str:
    if not history:
        return "无历史对话"
    lines = []
    for msg in history[-6:]:
        role = "用户" if msg.get("role") == "user" else "客服"
        content = msg.get("content", "")
        lines.append(f"{role}: {content[:200]}")
    return "\n".join(lines)


async def _stream_collect(llm: Any, messages: list) -> str:
    """流式调用 LLM 并收集完整响应"""
    full = ""
    async for chunk in llm.astream(messages):
        text = chunk.content if hasattr(chunk, "content") else str(chunk)
        if text:
            full += text
    return full.strip()


async def generate_reply(
        user_message: str,
        llm: Any,
        system_prompt: str,
        history: list[dict] | None = None,
) -> dict:
    logger.info("开始生成回复, user_message=%.100s...", user_message)
    try:
        messages = build_messages(history, system_prompt, user_message)
        text = await _stream_collect(llm, messages)
        result = _parse_json_response(text)
        logger.info("回复生成完成, content_len=%d", len(result.get("content", "")))
        return result
    except Exception:
        logger.exception("LLM 回复生成失败")
        raise


async def stream_generate_reply(
        user_message: str,
        llm: Any,
        system_prompt: str,
        history: list[dict] | None = None,
):
    """流式生成回复 — 使用 llm.astream() 实现真流式"""
    logger.info("开始流式生成回复, user_message=%.100s...", user_message)
    try:
        messages = build_messages(history, system_prompt, user_message)
        async for chunk in llm.astream(messages):
            text = chunk.content if hasattr(chunk, "content") else str(chunk)
            if text:
                yield text
    except Exception:
        logger.exception("流式回复生成失败")
        raise


async def recognize_intent(
        user_message: str,
        llm: Any,
        intent_prompt: str,
) -> dict:
    """识别用户意图 — 流式调用收集完整响应"""
    try:
        messages = [
            SystemMessage(content=intent_prompt),
            HumanMessage(content=user_message),
        ]
        text = await _stream_collect(llm, messages)
        result = _parse_json_response(text)
        intent = result.get("intent", "greeting")
        doc_type = result.get("doc_type") if intent == "knowledge_question" else None
        logger.info(
            "意图识别: intent=%s, doc_type=%s, confidence=%.2f",
            intent, doc_type, result.get("confidence", 0),
        )
        return {"intent": intent, "doc_type": doc_type, "confidence": result.get("confidence", 0)}
    except Exception:
        logger.warning("意图识别失败，默认为 greeting", exc_info=True)
        return {"intent": "greeting", "doc_type": None, "confidence": 0}


async def extract_lead_hint(
        assistant_reply: str,
        user_message: str,
        llm: Any,
        lead_hint_prompt: str,
        history: list[dict] | None = None,
) -> dict:
    """意向检测 — 流式调用收集完整响应"""
    try:
        tpl = Template(lead_hint_prompt)
        prompt = tpl.safe_substitute(
            user_message=str(user_message),
            assistant_reply=str(assistant_reply),
            history_summary=_summarize_history(history),
        )
        messages = [HumanMessage(content=prompt)]
        text = await _stream_collect(llm, messages)
        result = _parse_json_response(text)
        logger.debug("意向检测完成, should_ask=%s", result.get("should_ask"))
        return result
    except Exception:
        logger.warning("意向检测失败，使用默认值", exc_info=True)
        return {"should_ask": False, "message": "", "suggested_questions": []}
