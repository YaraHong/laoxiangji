from langchain_openai import ChatOpenAI

chat_model = ChatOpenAI(model="deepseek-v4-pro", streaming=True)

stream_llm_output = chat_model.stream("你好啊")

for chunk in stream_llm_output:
    print(chunk.content, end="")
