from typing import TypedDict, List, Optional, Annotated

from langgraph.graph import add_messages


class OverallStatePrivate(TypedDict):
    # 当前用户输入
    user_message: str

    # 历史消息
    messages: Annotated[list, add_messages]

    # 当前意图
    intent: Optional[str]

    # 是否转人工
    escalate_to_human: bool

    # 是否需要检索
    retrieval_required: bool

    # 检索结果
    retrieved_documents: List[str]

    # Prompt
    prompt: str

    # LLM输出
    llm_output: str

    # 是否需要追问
    need_followup: bool
