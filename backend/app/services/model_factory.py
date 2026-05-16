from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import settings


@lru_cache()
def _get_chat_llm(streaming: bool = False):
    return ChatOpenAI(
        model="qwen3.5-plus",
        api_key="sk-96ac50b53f414a6095151ece0eed52ce",
        streaming=streaming,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


@lru_cache()
def _get_embedding_model():
    return OpenAIEmbeddings(
        model="Qwen3-Embedding-8B",
        api_key="9ZR6MOAR4O1UIABK4PP1J1KZNCQLC7SYRNZLSY1S",
        base_url="https://ai.gitee.com/v1",
        default_headers={"X-Failover-Enabled": "true"},
    )


# 模块级实例（首次访问时通过 lru_cache 延迟初始化）
chat_llm = _get_chat_llm()
streaming_chat_llm = _get_chat_llm(streaming=True)
light_llm = _get_chat_llm()


def get_embedding_model_name() -> str:
    return settings.model.embedding_name


async def create_embedding(texts: list[str]) -> list[list[float]]:
    """批量文本嵌入 — 供 knowledge_service 使用"""
    model = _get_embedding_model()
    return await model.aembed_documents(texts)


async def embed_query(query: str) -> list[float]:
    """单条查询嵌入 — 供 rag_service 检索使用"""
    model = _get_embedding_model()
    return await model.aembed_query(query)
