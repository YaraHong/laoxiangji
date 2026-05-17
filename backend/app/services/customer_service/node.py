import time

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate

from app.services.customer_service.overall_state_private import OverallStatePrivate
from app.services.model_factory import chat_llm
from app.services.prompt_loader import load_prompt
from app.utils.logger_handle import logger

json_output_parser = JsonOutputParser()
str_output_parser = StrOutputParser()


class CustomerServiceNode:
    pass

    @staticmethod
    def intent_recognition(state: OverallStatePrivate):
        """
        做意图识别，根据当前用户输入判断用户意图以及是否需要向量检索、转人工
        """
        # 记录开始时间
        start_time = time.time()
        logger.info("【意图识别开始】")
        logger.info(f"当前状态：{state}")
        try:
            # 构建chain
            prompt = load_prompt("intent_recognition.txt")
            template = PromptTemplate.from_template(prompt)
            chain = template | chat_llm | json_output_parser

            # 构建对话变量
            conversation = "\n".join(
                f"{'用户' if isinstance(msg, HumanMessage) else '大模型'}: {msg.content}"
                for msg in state["messages"]
            )

            conversation += f"\n当前用户消息：{state['user_message']}"

            logger.info(
                f"提示词：\n{template.format(conversation=conversation)}"
            )

            # 解析结果
            llm_output_json = chain.invoke(
                input={"conversation": conversation}
            )

            # 更新状态
            state["intent"] = llm_output_json.get("intent")
            state["retrieval_required"] = llm_output_json.get("retrieval_required", False)
            state["escalate_to_human"] = llm_output_json.get("escalate_to_human", False)

            # 计算耗时
            elapsed_time = time.time() - start_time
            logger.info(f"【意图识别结束】耗时: {elapsed_time:.3f} 秒")
            logger.info(
                f"识别结果 - 意图: {state['intent']}, 需要检索: {state['retrieval_required']}, 转人工: {state['escalate_to_human']}"
            )

            return state

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.info(f"【意图识别异常结束】耗时: {elapsed_time:.3f} 秒, 错误: {str(e)}")
            raise

    @staticmethod
    def should_escalate_to_human(state: OverallStatePrivate):

        return state.get("escalate_to_human", False)

    @staticmethod
    def human_handling_node(state: OverallStatePrivate):
        """
        人工节点
        """
        logger.info("结束，跳转人工")

    @staticmethod
    def should_use_vector_search(state: OverallStatePrivate):
        """
        判断是否需要向量检索
        """
        return state.get("retrieval_required", False)

    @staticmethod
    def vector_retrieval(state: OverallStatePrivate):
        """
        向量检索
        """
        start_time = time.time()
        logger.info(f"【vector_retrieval开始】时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # state["retrieved_documents"] = ["暂无资料"]

        elapsed_time = time.time() - start_time
        logger.info(f"【vector_retrieval结束】耗时: {elapsed_time:.3f} 秒")

    @staticmethod
    def build_output_prompt(state: OverallStatePrivate):
        """
        构建提示词
        """
        logger.info("【构建提示词开始】")
        retrieval_required = state.get("retrieval_required", False)
        documents = state.get("retrieved_documents")

        if retrieval_required and documents is not None:
            material = ""
            if isinstance(documents, list):
                for index, document in enumerate(documents):
                    material += f"参考资料{index + 1}：\n" + document + "\n"
            else:
                material = "暂无资料提供"
        else:
            material = "暂无资料提供"

        prompt = load_prompt("rag_system_prompt.txt")
        template = PromptTemplate.from_template(prompt)

        formatted_prompt = template.format(material=material)

        state["prompt"] = formatted_prompt

        logger.info(f"提示词：\n{formatted_prompt}")

        return state

    # @staticmethod
    # async def llm_output(state: OverallStatePrivate):
    #     """
    #     调用大模型输出
    #     """
    #
    #     prompt = state.get("prompt", "")
    #
    #     llm_output = await streaming_chat_llm.ainvoke(prompt)
    #
    #     state["llm_output"] = llm_output.content
    #
    #     return state
