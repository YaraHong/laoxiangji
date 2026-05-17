from langchain_openai import ChatOpenAI, OpenAI

from app.core.config import settings

chat_llm = ChatOpenAI(
    model=settings.models.chat.model_name,
    base_url=settings.models.chat.base_url,
    api_key=settings.models.chat.api_key,
    temperature=0.7,
    max_tokens=2000,
    timeout=300
)

streaming_chat_llm = ChatOpenAI(
    model=settings.models.chat.model_name,
    base_url=settings.models.chat.base_url,
    api_key=settings.models.chat.api_key,
    temperature=0.7,
    max_tokens=2000,
    timeout=300,
    streaming=True
)

intent_llm = ChatOpenAI(
    model=settings.models.intent.model_name,
    base_url=settings.models.intent.base_url,
    api_key=settings.models.intent.api_key,
    temperature=0.7,
    max_tokens=2000,
    timeout=300,
    streaming=True
)

client = OpenAI(
    base_url='https://api-inference.modelscope.cn/v1',
    api_key='ms-62c5b98c-6b4b-4378-acf2-c70c4196c7b9',
)

embedding_model = client.embeddings.create(
    model='Qwen/Qwen3-Embedding-8B',
    input='你好',
    encoding_format="float",
    dimensions=1024
)
