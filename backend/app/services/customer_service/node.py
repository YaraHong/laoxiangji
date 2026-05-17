import asyncio
import time
from typing import Dict, AsyncGenerator

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.services.customer_service.overall_state_private import OverallStatePrivate
from app.services.model_factory import chat_llm, streaming_chat_llm
from app.services.prompt_loader import load_prompt
from app.utils.logger_handle import logger

json_output_parser = JsonOutputParser()


def intent_recognition(state: OverallStatePrivate) -> OverallStatePrivate:
    """
    意图识别节点
    """
    start_time = time.time()
    logger.info("【意图识别开始】")

    try:
        # 构建chain
        prompt = load_prompt("intent_recognition.txt")
        template = PromptTemplate.from_template(prompt)
        chain = template | chat_llm | json_output_parser

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

    except Exception as e:
        logger.exception(f"意图识别失败: {e}")
        raise


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
    """
    向量检索节点
    """
    try:
        logger.info("【向量检索开始】")
    except Exception as e:
        logger.error(f"向量检索失败: {e}")
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

    messages = [
        SystemMessage(content=state["prompt"]),
        HumanMessage(content=state["user_message"])
    ]

    full_response = ""

    try:
        async for chunk in streaming_chat_llm.astream(messages):
            if chunk.content:
                full_response += chunk.content
                yield {"llm_output": chunk.content}

        logger.info(f"【LLM输出结束】输出长度: {len(full_response)}字符")
        yield {"llm_output_final": full_response}

    except Exception as e:
        logger.error(f"LLM输出失败: {e}")
        yield {"llm_output_final": f"生成回复失败：{str(e)}"}


async def save_message(state: OverallStatePrivate) -> OverallStatePrivate:
    """保存消息节点：持久化对话消息"""
    logger.info("【保存消息开始】")

    try:
        # TODO: 替换为实际的消息保存逻辑
        await asyncio.sleep(0.1)  # 模拟异步操作

        # 保存用户消息和AI回复到数据库
        # await message_repository.save(state["user_message"], state.get("llm_output_final"))

        logger.info("【保存消息结束】")

    except Exception as e:
        logger.error(f"保存消息失败: {e}")

    return state


async def conversation_analysis(state: OverallStatePrivate) -> OverallStatePrivate:
    """
    对话分析节点：分析对话质量、用户满意度等

    可在对话结束后进行异步分析
    """
    logger.info("【对话分析开始】")

    try:
        # TODO: 替换为实际的分析逻辑
        await asyncio.sleep(0.1)  # 模拟异步操作

        # 分析对话意图识别准确率、回复质量等
        # analysis_result = analyze_conversation(state)

        logger.info("【对话分析结束】")

    except Exception as e:
        logger.error(f"对话分析失败: {e}")

    return state
