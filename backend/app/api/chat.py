import asyncio
import json
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger_handle import logger
from app.core.response import success
from app.models.rag_citation import RagCitation
from app.schemas.chat import (
    CreateMessageRequest,
    CreateSessionRequest,
    MessageResponse,
    SessionInfo,
)
from app.services.ai_service import extract_lead_hint, recognize_intent, stream_generate_reply
from app.services.chat_service import (
    create_session,
    get_cached_messages,
    get_session_with_messages,
    save_assistant_message,
    save_user_message,
)
from app.services.model_factory import light_llm, streaming_chat_llm
from app.services.prompt_loader import get_prompt
from app.services.rag_service import (
    build_citations_from_chunks,
    retrieve_from_milvus,
    stream_generate_rag_answer,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _build_message_response(msg) -> MessageResponse:
    meta = msg.message_metadata or {}
    return MessageResponse(
        id=msg.id,
        session_id=msg.session_id,
        role=msg.role,
        content=msg.content,
        message_type=msg.message_type,
        confidence=float(msg.confidence) if msg.confidence is not None else None,
        citations=meta.get("citations", []),
        created_at=msg.created_at,
    )


def _build_message_response_from_cache(data: dict) -> MessageResponse:
    return MessageResponse(
        id=data["id"],
        session_id=data.get("session_id", 0),
        role=data["role"],
        content=data["content"],
        message_type=data.get("message_type", "text"),
        citations=data.get("citations", []),
        created_at=data["created_at"],
    )


@router.post("/sessions")
async def create_chat_session(
        request: CreateSessionRequest,
        db: AsyncSession = Depends(get_db),
):
    session = await create_session(
        db, channel=request.channel, visitor_id=request.visitor_id
    )
    return success({"session_id": session.id, "session_no": session.session_no})


@router.get("/sessions/{session_id}")
async def get_chat_session(
        session_id: int,
        db: AsyncSession = Depends(get_db),
):
    session = await get_session_with_messages(db, session_id)
    cached = await get_cached_messages(db, session_id)
    messages = [_build_message_response_from_cache(m) for m in cached]
    return success(
        {
            "session": SessionInfo.model_validate(session).model_dump(),
            "messages": [m.model_dump() if hasattr(m, 'model_dump') else m for m in messages],
        }
    )


TRANSFER_MESSAGE = (
    "已收到您的转人工请求，招商经理将在工作时间内尽快与您联系。"
    "您也可以直接拨打加盟热线 400-xxx-xxxx 获取即时服务。"
)


@router.post("/sessions/{session_id}/messages/stream")
async def stream_chat_message(
        session_id: int,
        request: CreateMessageRequest,
        db: AsyncSession = Depends(get_db),
):
    await save_user_message(db, session_id, request.content)

    cached = await get_cached_messages(db, session_id)
    history = [
        {"role": m.get("role"), "content": m.get("content")}
        for m in cached
        if m.get("role") in ("user", "assistant")
    ]

    stream_prompt = get_prompt("chat_system")
    rag_prompt = get_prompt("rag_system")
    lead_prompt = get_prompt("lead_hint")
    intent_prompt = get_prompt("intent_recognition")

    # 意图识别 — 使用轻量流式实例
    t0 = time.perf_counter()
    intent_result = await recognize_intent(request.content, light_llm, intent_prompt)
    intent = intent_result["intent"]
    doc_type = intent_result.get("doc_type")
    t_intent = (time.perf_counter() - t0) * 1000

    logger.info("会话 %d 意图识别耗时: %.0fms, intent=%s, doc_type=%s", session_id, t_intent, intent, doc_type)

    async def event_stream():
        full_reply = ""
        citations = []

        try:
            # 如果判断出要转人工，直接返回
            if intent == "transfer_human":
                full_reply = TRANSFER_MESSAGE
                yield f"event: transfer\ndata: {json.dumps({'message': '已转接人工客服'}, ensure_ascii=False)}\n\n"
                async for chunk in _stream_text(full_reply):
                    yield chunk

            # 根据意图识别，从向量库中查询
            elif intent == "knowledge_question":
                chunks = await retrieve_from_milvus(
                    request.content,
                    top_k=5,
                    doc_type=doc_type,
                )
                logger.info("会话 %d RAG检索: filter=%s, chunks=%d", session_id, doc_type, len(chunks))

                t_gen = time.perf_counter()
                if chunks:
                    stream_gen = stream_generate_rag_answer(
                        request.content, chunks, streaming_chat_llm, rag_prompt, history=history
                    )
                else:
                    stream_gen = stream_generate_reply(
                        request.content, streaming_chat_llm, stream_prompt, history=history
                    )

                async for text_chunk in stream_gen:
                    full_reply += text_chunk
                    yield f"event: content\ndata: {json.dumps({'text': text_chunk}, ensure_ascii=False)}\n\n"

                t_reply = (time.perf_counter() - t_gen) * 1000
                logger.info("会话 %d 回复生成耗时: %.0fms, reply_len=%d", session_id, t_reply, len(full_reply))

                citations = build_citations_from_chunks(chunks, min_score=0.4) if chunks else []
                yield f"event: citations\ndata: {json.dumps(citations, ensure_ascii=False)}\n\n"

            # 如果不是查询，例如只是打招呼，直接调用大模型回复
            else:
                t_gen = time.perf_counter()
                stream_gen = stream_generate_reply(
                    request.content, streaming_chat_llm, stream_prompt, history=history
                )
                async for text_chunk in stream_gen:
                    full_reply += text_chunk
                    yield f"event: content\ndata: {json.dumps({'text': text_chunk}, ensure_ascii=False)}\n\n"

                t_reply = (time.perf_counter() - t_gen) * 1000
                logger.info("会话 %d 回复生成耗时: %.0fms, reply_len=%d", session_id, t_reply, len(full_reply))

            if not full_reply:
                full_reply = "系统异常，请重新提问"

            t_hint = time.perf_counter()
            lead_hint = await extract_lead_hint(
                full_reply, request.content, light_llm, lead_prompt, history
            )
            t_lead_hint = (time.perf_counter() - t_hint) * 1000
            logger.info("会话 %d 意向检测耗时: %.0fms", session_id, t_lead_hint)
            yield f"event: lead_hint\ndata: {json.dumps(lead_hint, ensure_ascii=False)}\n\n"

            assistant_msg = await save_assistant_message(
                db, session_id,
                content=full_reply,
                message_type="text",
                citations=citations,
                lead_hint=lead_hint,
            )
            logger.info(
                "会话%d流式完成: intent=%s, msg_id=%d, reply_len=%d", session_id, intent, assistant_msg.id,
                len(full_reply)
            )

            if citations:
                db.add_all([
                    RagCitation(
                        message_id=assistant_msg.id,
                        chunk_id=0,
                        document_title=cit["title"],
                        score=0.0,
                        snippet=cit.get("snippet", ""),
                    )
                    for cit in citations
                ])
                await db.commit()

            yield f"event: meta\ndata: {json.dumps({'message_id': assistant_msg.id, 'done': True, 'intent': intent})}\n\n"

        except Exception:
            logger.exception("会话 %d 流式异常, intent=%s, 已生成内容长度=%d", session_id, intent, len(full_reply))
            yield f"event: error\ndata: {json.dumps({'message': '生成回复时出现错误，请稍后重试'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _stream_text(text: str):
    """将文本以流式 chunk 输出"""
    chunk_size = 3
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        yield f"event: content\ndata: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.02)
