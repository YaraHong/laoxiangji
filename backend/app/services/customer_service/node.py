import json
import time

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
        logger.info(f"【意图识别开始】时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"当前状态：{state}")
        try:
            # 构建chain
            prompt = load_prompt("intent_recognition.txt")
            template = PromptTemplate.from_template(prompt)
            chain = template | chat_llm | json_output_parser

            # 构建对话变量
            conversation = "\n".join(
                f"{'用户' if msg['role'] == 'user' else '大模型'}:{msg['content']}"
                for msg in state["messages"]
            )

            conversation += f'\n当前用户消息：{state["user_message"]}'
            logger.info(f"提示词：\n{template.format(conversation=conversation)}")
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
        """
        判断是否需要人工，如果需要人工就跳转人工
        """
        start_time = time.time()
        logger.info(f"【should_escalate_to_human开始】时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        escalate_to_human = state.get("escalate_to_human", False)

        if escalate_to_human:
            result = "human_handling_node"
        else:
            result = "should_use_vector_search"

        elapsed_time = time.time() - start_time
        logger.info(f"【should_escalate_to_human结束】耗时: {elapsed_time:.3f} 秒, 返回: {result}")

        return result

    @staticmethod
    def human_handling_node(state: OverallStatePrivate):
        """
        人工节点
        """
        start_time = time.time()
        logger.info(f"【human_handling_node开始】时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # TODO 转到人工 ，graph 直接结束

        elapsed_time = time.time() - start_time
        logger.info(f"【human_handling_node结束】耗时: {elapsed_time:.3f} 秒")

    @staticmethod
    def should_use_vector_search(state: OverallStatePrivate):
        """
        判断是否需要向量检索
        """
        start_time = time.time()
        logger.info(f"【should_use_vector_search开始】时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        retrieval_required = state.get("retrieval_required", False)

        if retrieval_required:
            result = "vector_retrieval"
        else:
            result = "build_output_prompt"

        elapsed_time = time.time() - start_time
        logger.info(f"【should_use_vector_search结束】耗时: {elapsed_time:.3f} 秒, 返回: {result}")

        return result

    @staticmethod
    def vector_retrieval(state: OverallStatePrivate):
        """
        向量检索
        """
        start_time = time.time()
        logger.info(f"【vector_retrieval开始】时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        state["retrieved_documents"] = ["暂无资料"]

        elapsed_time = time.time() - start_time
        logger.info(f"【vector_retrieval结束】耗时: {elapsed_time:.3f} 秒")

    @staticmethod
    def build_output_prompt(state: OverallStatePrivate):
        """
        构建提示词
        """
        try:
            start_time = time.time()
            logger.info(f"【build_output_prompt开始】时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

            documents = state.get("retrieved_documents")

            if documents:
                material = ""
                for index, document in documents:
                    material += f"参考资料{index}：\n" + document + "\n"
            else:
                material = "暂无资料提供"

            prompt = load_prompt("rag_system_prompt.txt")
            template = PromptTemplate.from_template(prompt)
            prompt_value = template.invoke(input={"material": material})

            state["prompt"] = prompt_value

            elapsed_time = time.time() - start_time
            logger.info(f"【build_output_prompt结束】耗时: {elapsed_time:.3f} 秒")
        except Exception as e:
            logger.error(e)

    @staticmethod
    async def llm_output(state: OverallStatePrivate):
        """
        调用大模型输出
        """
        start_time = time.time()
        logger.info(f"【llm_output开始】时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        prompt = state.get("prompt", "")

        # 异步流式输出
        async for chunk in chat_llm.astream(prompt):
            # 注意：LangGraph 节点返回应该是字典，不是 yield
            # 你需要用回调或特殊处理
            print(chunk)
            yield chunk  # 这里会有问题

        elapsed_time = time.time() - start_time
        logger.info(f"【llm_output结束】耗时: {elapsed_time:.3f} 秒")
