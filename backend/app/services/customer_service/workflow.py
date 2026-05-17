from langchain_core.messages import HumanMessage, AIMessage
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger_handle import logger
from app.services import (
    save_user_message,
    get_cached_messages, save_assistant_message
)
from app.services.customer_service.node import (
    intent_recognition,
    should_escalate_to_human,
    human_handling_node,
    should_use_vector_search,
    vector_retrieval,
    build_output_prompt,
    llm_output_node
)
from app.services.customer_service.overall_state_private import OverallStatePrivate


async def run_customer_pipeline(
        db: AsyncSession,
        session_id,
        content
):
    # 保存用户消息
    await save_user_message(db, session_id, content)

    # 获取最近10轮对话
    history_msg = await get_cached_messages(db, session_id)

    messages = []

    # 处理一下历史对话，放到state中
    for msg in history_msg:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))

        else:
            messages.append(AIMessage(content=msg["content"]))

    # graph
    builder = StateGraph(OverallStatePrivate)
    # 意图识别
    builder.add_node("intent_recognition", intent_recognition)
    # 人工处理节点
    builder.add_node("human_handling_node", human_handling_node)
    # 向量检索节点
    builder.add_node("vector_retrieval", vector_retrieval)
    # 构建提示词节点
    builder.add_node("build_output_prompt", build_output_prompt)
    # 调用大模型生成回复节点
    builder.add_node("llm_output", llm_output_node)
    # 先做意图识别
    builder.add_edge(START, "intent_recognition")
    # 根据识别结果判断转人工，还是下一步
    builder.add_conditional_edges(
        "intent_recognition",
        should_escalate_to_human,
        {
            True: "human_handling_node",
            False: "vector_retrieval"
        }
    )
    # 如果是人工，结束
    builder.add_edge("human_handling_node", END)

    builder.add_conditional_edges(
        "vector_retrieval",
        should_use_vector_search,
        {
            True: "build_output_prompt",
            False: "build_output_prompt"
        }
    )

    builder.add_edge("build_output_prompt", "llm_output")
    builder.add_edge("llm_output", END)

    graph = builder.compile()

    logger.info(f"\n{graph.get_graph().draw_ascii()}")

    state = OverallStatePrivate(
        user_message=content,
        messages=messages,
        intent=None,
        retrieval_required=False,
        escalate_to_human=False,
        retrieved_documents=[],
        prompt="",
        llm_output="",
        need_followup=False,
    )

    content = ""
    async for event in graph.astream_events(state, version="v2"):
        event_type = event["event"]

        if event_type == "on_chain_stream":
            data = event.get("data", {})
            chunk = data.get("chunk")

            if isinstance(chunk, dict):
                token = chunk.get("llm_output")
                if token:
                    content += token
                    yield f"data: {token}\n\n"

    # 保存大模型消息
    await save_assistant_message(db, session_id, content)
    yield "data: [DONE]\n\n"
