import json

from langgraph.constants import START, END
from langgraph.graph import StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import save_user_message, get_cached_messages
from app.services.customer_service.node import CustomerServiceNode
from app.services.customer_service.overall_state_private import OverallStatePrivate
from app.utils.logger_handle import logger


async def run_customer_pipeline(db: AsyncSession, session_id, content):
    # 保存当前消息
    await save_user_message(db, session_id, content)

    # 获取最近10轮对话
    history_msg = await get_cached_messages(db, session_id)

    # 构建图
    builder = StateGraph(OverallStatePrivate)

    # 意图识别节点
    builder.add_node("intent_recognition", CustomerServiceNode.intent_recognition)
    # 人工处理节点
    builder.add_node("human_handling_node", CustomerServiceNode.human_handling_node)
    # 向量查询节点
    builder.add_node("vector_retrieval", CustomerServiceNode.vector_retrieval)
    # 构建提示词节点
    builder.add_node("build_output_prompt", CustomerServiceNode.build_output_prompt)
    # 大模型输出节点
    builder.add_node("llm_output", CustomerServiceNode.llm_output)

    # 用来衔接两个条件边
    builder.add_node("routing_decision", lambda state: state)  # 空节点，什么都不做

    # 先做意图识别
    builder.add_edge(START, "intent_recognition")

    # 根据意图识别判断是否需要转人工
    builder.add_conditional_edges(
        "intent_recognition",
        CustomerServiceNode.should_escalate_to_human,
        {
            True: "human_handling_node",
            False: "routing_decision"
        }
    )

    # 如果需要转人工，直接结束
    builder.add_edge("human_handling_node", END)

    # 判断是否需要向量库查询
    builder.add_conditional_edges(
        "routing_decision",
        CustomerServiceNode.should_use_vector_search,
        {
            True: "vector_retrieval",
            False: "build_output_prompt"
        }
    )

    builder.add_edge("vector_retrieval", "build_output_prompt")
    builder.add_edge("build_output_prompt", "llm_output")
    builder.add_edge("llm_output", END)

    # 编译图
    graph = builder.compile()

    logger.info(graph.get_graph().draw_ascii())
    # 初始化状态
    state = OverallStatePrivate(
        user_message=content,
        messages=history_msg,
        intent=None,
        retrieval_required=False,
        escalate_to_human=False,
        need_followup=False,
    )

    # 执行
    async for chunk in graph.astream(state):
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
