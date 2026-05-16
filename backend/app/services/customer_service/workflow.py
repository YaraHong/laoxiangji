import json

from langgraph.constants import START, END
from langgraph.graph import StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import save_user_message, get_cached_messages
from app.services.customer_service.node import CustomerServiceNode
from app.services.customer_service.overall_state_private import OverallStatePrivate


async def run_customer_pipeline(db: AsyncSession, session_id, content):
    # 保存当前消息
    await save_user_message(db, session_id, content)

    # 获取最近10轮对话
    history_msg = await get_cached_messages(db, session_id)

    # 构建图
    builder = StateGraph(OverallStatePrivate)

    # 添加普通节点
    builder.add_node("intent_recognition", CustomerServiceNode.intent_recognition)
    builder.add_node("human_handling_node", CustomerServiceNode.human_handling_node)
    builder.add_node("vector_retrieval", CustomerServiceNode.vector_retrieval)
    builder.add_node("build_output_prompt", CustomerServiceNode.build_output_prompt)
    builder.add_node("llm_output", CustomerServiceNode.llm_output)

    # ⭐ 添加一个空的"路由决策"节点，用于连接两个条件边
    builder.add_node("routing_decision", lambda state: state)  # 空节点，什么都不做

    # 开始
    builder.add_edge(START, "intent_recognition")

    # ✅ 第一个条件边：判断是否需要转人工
    builder.add_conditional_edges(
        "intent_recognition",
        CustomerServiceNode.should_escalate_to_human,
        {
            "human_handling_node": "human_handling_node",  # 转人工
            "should_use_vector_search": "routing_decision"  # 继续到第二个判断
        }
    )

    builder.add_edge("human_handling_node", END)

    # ✅ 第二个条件边：从 routing_decision 节点出发，判断是否需要向量检索
    builder.add_conditional_edges(
        "routing_decision",  # 源节点：空节点
        CustomerServiceNode.should_use_vector_search,  # 判断函数
        {
            "vector_retrieval": "vector_retrieval",  # 需要向量检索
            "build_output_prompt": "build_output_prompt"  # 直接构建提示词
        }
    )

    # 后续流程
    builder.add_edge("vector_retrieval", "build_output_prompt")
    builder.add_edge("build_output_prompt", "llm_output")
    builder.add_edge("llm_output", END)

    # 编译图
    graph = builder.compile()

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
