import asyncio
from fastmcp import Client

client = Client("http://localhost:3345/engineering/mcp")


async def call_tool():
    async with client:
        result = await client.call_tool("tool_search", {"query": "桥涵 横向车道系数"})
        print(result)


asyncio.run(call_tool())
