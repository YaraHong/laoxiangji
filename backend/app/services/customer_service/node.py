import time
from typing import Dict, AsyncGenerator

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.core.logger_handle import logger
from app.core.milvus import get_collection
from app.core.model_factory import streaming_chat_llm, intent_llm, openai_client
from app.services.customer_service.overall_state_private import OverallStatePrivate
from app.services.prompt_loader import load_prompt

json_output_parser = JsonOutputParser()


def intent_recognition(state: OverallStatePrivate) -> OverallStatePrivate:
    """
    意图识别节点
    """
    start_time = time.time()
    logger.info("【意图识别开始】")
    # 构建chain
    prompt = load_prompt("intent_recognition.txt")
    template = PromptTemplate.from_template(prompt)
    chain = template | intent_llm | json_output_parser

    # 构建对话历史上下文
    conversation = "\n".join(
        f"{'用户' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}"
        for msg in state["messages"]
    )
    conversation += f"\n当前用户消息：{state['user_message']}"

    # 调用LLM进行意图识别
    llm_output = chain.invoke(input={"conversation": conversation})

    # 更新状态
    state["intent"] = llm_output.get("intent")
    state["retrieval_required"] = llm_output.get("retrieval_required", False)
    state["escalate_to_human"] = llm_output.get("escalate_to_human", False)

    elapsed_time = time.time() - start_time
    logger.info(f"【意图识别结束】意图: {state['intent']}, 耗时: {elapsed_time:.3f}秒")

    return state


def should_escalate_to_human(state: OverallStatePrivate) -> bool:
    """判断是否需要转人工"""
    return state.get("escalate_to_human", False)


def should_use_vector_search(state: OverallStatePrivate) -> bool:
    """判断是否需要使用向量检索"""
    return state.get("retrieval_required", False)


def human_handling_node(state: OverallStatePrivate) -> OverallStatePrivate:
    """人工处理节点"""
    logger.info(f"【转人工】")
    return state


def vector_retrieval(state: OverallStatePrivate) -> OverallStatePrivate:
    try:
        logger.info("【向量检索开始 - Milvus】")

        prompt = load_prompt("context_rewriting.txt")
        template = PromptTemplate.from_template(prompt)
        chain = template | intent_llm | json_output_parser

        result_json = chain.invoke(
            input={"user_input": state["user_message"]}
        )

        query = result_json.get("query_rewrite", state["user_message"])
        doctype = result_json.get("doctype", [])

        embedding_response = openai_client.embeddings.create(
            model='Qwen/Qwen3-Embedding-8B',
            input=query,
            encoding_format="float",
            dimensions=1024
        )

        pure_vector = embedding_response.data[0].embedding

        expr = None
        if doctype:
            doctype_str = ", ".join([f"'{d}'" for d in doctype])
            expr = f"doc_type in [{doctype_str}]"

        col = get_collection()

        results = col.search(
            data=[pure_vector],
            anns_field="vector",
            param={
                "metric_type": "IP",
                "params": {"nprobe": 10}
            },
            limit=5,
            expr=expr,
            output_fields=["content", "doc_type"]
        )

        retrieved_contents = []
        if results and len(results) > 0:
            for hit in results[0]:
                content_text = hit.entity.get("content")
                if content_text:
                    retrieved_contents.append(content_text)

        # 写回 state
        state["retrieved_documents"] = retrieved_contents

        logger.info("【向量检索完成 - Milvus】")

    except Exception as e:
        logger.error(f"向量检索失败: {e}", exc_info=True)
        state["retrieved_documents"] = []

    return state


def build_output_prompt(state: OverallStatePrivate) -> OverallStatePrivate:
    """
    构建输出提示词
    """

    # 构建资料上下文
    retrieval_required = state.get("retrieval_required", False)
    documents = state.get("retrieved_documents", [])

    if retrieval_required and documents:
        material_parts = []
        for index, document in enumerate(documents):
            material_parts.append(f"参考资料{index + 1}：\n{document}\n")
        material = "\n".join(material_parts)
    else:
        material = "暂无资料"

    prompt_template = load_prompt("rag_system_prompt.txt")
    template = PromptTemplate.from_template(prompt_template)
    formatted_prompt = template.format(material=material)

    state["prompt"] = formatted_prompt

    return state


async def llm_output_node(state: OverallStatePrivate) -> AsyncGenerator[Dict[str, str], None]:
    """
    LLM流式输出节点：生成并输出回复内容
    """
    logger.info("【LLM输出开始】")
    logger.info(state["prompt"])
    messages = [
        SystemMessage(content=state["prompt"]),
        HumanMessage(content=state["user_message"])
    ]

    full_response = ""

    async for chunk in streaming_chat_llm.astream(messages):
        if chunk.content:
            full_response += chunk.content
            yield {"llm_output": chunk.content}

    yield {"llm_output_final": full_response}
