import asyncio
import time

from langchain_core.messages import (
    HumanMessage,
    SystemMessage
)

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.services.customer_service.overall_state_private import OverallStatePrivate

from app.services.model_factory import (
    chat_llm,
    streaming_chat_llm
)

from app.services.prompt_loader import load_prompt

from app.utils.logger_handle import logger

json_output_parser = JsonOutputParser()


def intent_recognition(
        state: OverallStatePrivate
):

    start_time = time.time()

    logger.info("【意图识别开始】")

    try:

        prompt = load_prompt(
            "intent_recognition.txt"
        )

        template = PromptTemplate.from_template(
            prompt
        )

        chain = (
                template
                | chat_llm
                | json_output_parser
        )

        conversation = "\n".join(
            f"{'用户' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}"
            for msg in state["messages"]
        )

        conversation += (
            f"\n当前用户消息：{state['user_message']}"
        )

        llm_output_json = chain.invoke(
            input={
                "conversation": conversation
            }
        )

        state["intent"] = llm_output_json.get(
            "intent"
        )

        state["retrieval_required"] = (
            llm_output_json.get(
                "retrieval_required",
                False
            )
        )

        state["escalate_to_human"] = (
            llm_output_json.get(
                "escalate_to_human",
                False
            )
        )

        elapsed_time = (
                time.time() - start_time
        )

        logger.info(
            f"【意图识别结束】耗时: {elapsed_time:.3f} 秒"
        )

        return state

    except Exception as e:

        logger.exception(e)

        raise


def should_escalate_to_human(
        state: OverallStatePrivate
):

    return state.get(
        "escalate_to_human",
        False
    )


def human_handling_node(
        state: OverallStatePrivate
):

    logger.info("【转人工】")

    return state


def should_use_vector_search(
        state: OverallStatePrivate
):

    return state.get(
        "retrieval_required",
        False
    )


def vector_retrieval(
        state: OverallStatePrivate
):

    logger.info("【向量检索开始】")

    state["retrieved_documents"] = [
        "加盟需要满足以下条件：..."
    ]

    logger.info("【向量检索结束】")

    return state


def build_output_prompt(
        state: OverallStatePrivate
):

    logger.info("【Prompt构建开始】")

    retrieval_required = state.get(
        "retrieval_required",
        False
    )

    documents = state.get(
        "retrieved_documents"
    )

    if retrieval_required and documents:

        material = ""

        for index, document in enumerate(
                documents
        ):
            material += (
                f"参考资料{index + 1}：\n"
                f"{document}\n"
            )

    else:

        material = "暂无资料"

    prompt = load_prompt(
        "rag_system_prompt.txt"
    )

    template = PromptTemplate.from_template(
        prompt
    )

    formatted_prompt = template.format(
        material=material
    )

    state["prompt"] = formatted_prompt

    logger.info(
        f"Prompt:\n{formatted_prompt}"
    )

    return state


# 核心流式节点
async def llm_output_node(
        state: OverallStatePrivate
):

    logger.info("【LLM输出开始】")

    full_response = ""

    messages = [
        SystemMessage(
            content=state["prompt"]
        ),
        HumanMessage(
            content=state["user_message"]
        )
    ]

    async for chunk in streaming_chat_llm.astream(
            messages
    ):

        if chunk.content:

            full_response += chunk.content

            # 增量流式输出
            yield {
                "llm_output": chunk.content
            }

    logger.info("【LLM输出结束】")

    # 最终完整结果
    yield {
        "llm_output_final": full_response
    }


async def save_message(
        state: OverallStatePrivate
):

    logger.info("【保存消息开始】")

    await asyncio.sleep(1)

    logger.info("【保存消息结束】")

    return state


async def conversation_analysis(
        state: OverallStatePrivate
):

    logger.info("【对话分析开始】")

    await asyncio.sleep(1)

    logger.info("【对话分析结束】")

    return state