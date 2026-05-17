from langchain_core.messages import (
    HumanMessage,
    AIMessage
)

from langgraph.constants import START, END
from langgraph.graph import StateGraph

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import (
    save_user_message,
    get_cached_messages
)

from app.services.customer_service.node import (
    intent_recognition,
    should_escalate_to_human,
    human_handling_node,
    should_use_vector_search,
    vector_retrieval,
    build_output_prompt,
    llm_output_node,
    save_message,
    conversation_analysis
)

from app.services.customer_service.overall_state_private import OverallStatePrivate

from app.utils.logger_handle import logger


async def run_customer_pipeline(
        db: AsyncSession,
        session_id,
        content
):

    # 保存用户消息
    await save_user_message(
        db,
        session_id,
        content
    )

    # 获取历史消息
    history_msg = await get_cached_messages(
        db,
        session_id
    )

    messages = []

    for msg in history_msg:

        if msg["role"] == "user":

            messages.append(
                HumanMessage(
                    content=msg["content"]
                )
            )

        else:

            messages.append(
                AIMessage(
                    content=msg["content"]
                )
            )

    # graph
    builder = StateGraph(
        OverallStatePrivate
    )

    builder.add_node(
        "intent_recognition",
        intent_recognition
    )

    builder.add_node(
        "human_handling_node",
        human_handling_node
    )

    builder.add_node(
        "vector_retrieval",
        vector_retrieval
    )

    builder.add_node(
        "build_output_prompt",
        build_output_prompt
    )

    builder.add_node(
        "llm_output",
        llm_output_node
    )

    builder.add_node(
        "save_message",
        save_message
    )

    builder.add_node(
        "conversation_analysis",
        conversation_analysis
    )

    # graph结构
    builder.add_edge(
        START,
        "intent_recognition"
    )

    builder.add_conditional_edges(
        "intent_recognition",
        should_escalate_to_human,
        {
            True: "human_handling_node",
            False: "vector_retrieval"
        }
    )

    builder.add_edge(
        "human_handling_node",
        END
    )

    builder.add_conditional_edges(
        "vector_retrieval",
        should_use_vector_search,
        {
            True: "build_output_prompt",
            False: "build_output_prompt"
        }
    )

    builder.add_edge(
        "build_output_prompt",
        "llm_output"
    )

    builder.add_edge(
        "llm_output",
        "save_message"
    )

    builder.add_edge(
        "save_message",
        "conversation_analysis"
    )

    builder.add_edge(
        "conversation_analysis",
        END
    )

    graph = builder.compile()

    logger.info(
        graph.get_graph().draw_ascii()
    )

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

    # 核心
    async for event in graph.astream_events(
            state,
            version="v2"
    ):

        event_type = event["event"]

        # print(event)

        # 节点流式输出
        if event_type == "on_chain_stream":

            data = event.get(
                "data",
                {}
            )

            chunk = data.get(
                "chunk"
            )

            if isinstance(chunk, dict):

                token = chunk.get(
                    "llm_output"
                )

                if token:

                    yield f"data: {token}\n\n"

    # 结束标记
    yield "data: [DONE]\n\n"