from typing import TypedDict, List, Optional

from langchain_core.prompt_values import PromptValue


class OverallStatePrivate(TypedDict):
    # 当前用户输入消息
    user_message: str

    # 对话历史
    messages: List[dict]

    # 当前意图
    intent: Optional[str]

    # 是否需要转人工
    escalate_to_human: bool

    # 是否需要向量库检索
    retrieval_required: bool

    # 检索到的资料
    retrieved_documents: List[str]

    # 提示词
    prompt: PromptValue

    # 是否需要追问
    need_followup: bool
