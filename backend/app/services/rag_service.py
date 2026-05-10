from typing import Any

from app.core.logger_handle import logger
from app.core.milvus import get_collection
from app.services.ai_service import build_messages
from app.services.model_factory import embed_query


def _build_references(chunks: list[dict]) -> str:
    ref_lines = []
    seen = set()
    for i, c in enumerate(chunks, 1):
        if c["content"] not in seen:
            seen.add(c["content"])
            ref_lines.append(
                f"[{i}] 来源: {c['title']} | 类型: {c['doc_type']}\n{c['content']}"
            )
    return "\n\n---\n\n".join(ref_lines) if ref_lines else "（未检索到相关参考资料）"


async def retrieve_from_milvus(
        query: str,
        top_k: int = 5,
        doc_type: str | None = None,
) -> list[dict]:
    try:
        vector = await embed_query(query)
        logger.debug("Embedding 成功, dims=%d, query=%.50s...", len(vector), query)
    except Exception:
        logger.warning("Embedding 调用失败, query=%.50s...", query, exc_info=True)
        return []

    try:
        col = get_collection()
        search_params = {
            "data": [vector],
            "anns_field": "vector",
            "param": {"metric_type": "IP", "params": {"nprobe": 8}},
            "limit": top_k,
            "output_fields": ["doc_id", "chunk_index", "content", "title", "doc_type"],
        }
        if doc_type:
            search_params["expr"] = f'doc_type == "{doc_type}"'

        results = col.search(**search_params)
        chunks = []
        for hits in results:
            for hit in hits:
                chunks.append({
                    "score": hit.score,
                    "doc_id": hit.entity.get("doc_id"),
                    "chunk_index": hit.entity.get("chunk_index"),
                    "content": hit.entity.get("content"),
                    "title": hit.entity.get("title"),
                    "doc_type": hit.entity.get("doc_type"),
                })
        logger.info(
            "Milvus 检索完成, query=%.50s..., filter=%s, hits=%d, top_score=%.3f",
            query,
            doc_type or "无",
            len(chunks), chunks[0]["score"] if chunks else 0
        )
        return chunks
    except Exception:
        logger.warning("Milvus 搜索失败", exc_info=True)
        return []


def build_citations_from_chunks(chunks: list[dict], min_score: float = 0.4) -> list[dict]:
    citations = []
    seen_titles = set()
    for c in chunks:
        if c["score"] < min_score:
            continue
        title = c.get("title", "未知文档")
        if title in seen_titles:
            continue
        seen_titles.add(title)
        citations.append({
            "title": title,
            "snippet": c.get("content", "")[:100],
            "url": None,
        })
    return citations


async def stream_generate_rag_answer(
        user_message: str,
        chunks: list[dict],
        llm: Any,
        system_prompt: str,
        history: list[dict] | None = None,
):
    """流式生成 RAG 回复 — 使用 llm.astream() 实现真流式"""
    logger.info("开始流式生成 RAG 回复, chunks=%d", len(chunks))
    try:
        references = _build_references(chunks)
        system = system_prompt + f"\n\n## 参考资料\n{references}"
        messages = build_messages(history, system, user_message)

        async for chunk in llm.astream(messages):
            text = chunk.content if hasattr(chunk, "content") else str(chunk)
            if text:
                yield text
    except Exception:
        logger.exception("流式 RAG 回复生成失败")
        raise
