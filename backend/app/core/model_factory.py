from langchain_community.chat_models import ChatTongyi
from openai import OpenAI

chat_llm = ChatTongyi(
    model="deepseek-v4-pro"
)

streaming_chat_llm = ChatTongyi(
    model="deepseek-v4-pro",
    streaming=True
)

intent_llm = ChatTongyi(
    model="deepseek-v4-flash"
)

openai_client = OpenAI(
    base_url='https://api-inference.modelscope.cn/v1',
    api_key='ms-62c5b98c-6b4b-4378-acf2-c70c4196c7b9',
)
