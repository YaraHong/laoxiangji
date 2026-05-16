import asyncio
from langchain_openai import ChatOpenAI


async def main():
    llm = ChatOpenAI(
        model="deepseek-v4-pro",
        streaming=True,
    )

    async for chunk in llm.astream("你好，请介绍一下你自己"):
        print(chunk.content, end="", flush=True)


asyncio.run(main())
