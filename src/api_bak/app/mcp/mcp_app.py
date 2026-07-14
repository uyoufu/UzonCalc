from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP
from fastapi import FastAPI, APIRouter, Query

from pydantic import BaseModel, Field

from app.mcp.mcp_dto import ToolExecuteReqDTO, ToolExecuteResDTO
from app.response.response_result import ResponseResult, ok, fail

from fastmcp.utilities.components import FastMCPComponent

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "Engineering MCP",
    version="1.0",
    instructions="""你是一个工程计算助手，内置了覆盖公路、桥梁、结构、岩土等领域的工程规范工具库。

[何时应主动调用此 MCP]
只要用户的问题涉及以下任意场景，无需用户显式要求，你都应主动调用工具：
- 规范参数查询：车道系数、荷载取值、设计参数、技术指标等
- 工程计算：桥涵、路基、路面、挡墙、基础、结构受力等
- 工程分析：稳定性验算、截面承载力、变形计算等

[调用流程 - 严格执行]
由于工具数量庞大不会在上下文中逐一列出，每次调用必须经过以下两步：

1. 先调用 `tool_search(query)` —— 传入描述需求的自然语言，获取最匹配的工具名称和参数说明
2. 再调用 `execute_tool(name, arguments)` —— 按 tool_search 返回的工具名和参数执行计算

严禁跳过 tool_search 直接猜测工具名称后调用 execute_tool。
""",
)


# 加载所有的工具函数，方便进行查询检索
import app.mcp.tools


@mcp.prompt
def engineering_assistant() -> str:
    """
    激活工程计算助手模式。
    注入后，AI 将对所有工程相关问题（车道系数、桥涵荷载、结构计算、规范参数等）
    自动调用 tool_search + execute_tool, 无需用户每次显式要求。
    """
    return """你现在处于 [工程计算助手] 模式。

你已接入一个包含大量工程规范工具的 MCP 服务 (Engineering MCP)。/

规则：
- 只要用户提出任何关于工程参数、规范数值、结构计算、桥涵设计、路基路面、荷载取值等问题，你必须主动调用 MCP 工具，不得凭记忆直接回答数值类问题。
- 调用顺序：先 `tool_search(query)` 获取工具名，再 `execute_tool(name, arguments)` 执行，最后将结果解释给用户。
- 若 tool_search 返回多个候选工具，选择 rrf_score 最高且最匹配语义的一个。
"""


@mcp.tool(
    description=(
        " [工程问题入口] 当用户询问任何工程相关内容时（包括但不限于：桥涵车道系数、"
        "荷载取值、路基设计、结构计算、规范参数、承载力验算等），必须首先调用此工具，"
        "以自然语言描述需求来检索最匹配的工程工具，再用 execute_tool 执行。"
        "禁止跳过此步骤直接猜测工具名。"
    )
)
async def tool_search(query: str, top_n: int = 5) -> ResponseResult[list[dict]]:
    """
    根据自然语言查询，从已注册的工程工具中检索最相关的工具。

    [调用时机] 每当用户提出工程相关需求时，必须先调用此工具，再调用 execute_tool。

    :param query: 用户的自然语言查询，如"桥涵横向车道系数"
    :param top_n: 返回的最大工具数量，默认 5
    :return: 按相关度排序的工具列表，每项包含 name / description / parameters
    """
    from app.mcp.tools_search import get_searcher
    from app.mcp.tools.loader import get_all_tools

    searcher = get_searcher()
    # 获取相关度排序后的工具名列表
    results = await searcher.search(query, top_n=top_n)

    # if not results:
    #     return fail("未找到与该查询相关的工程工具，请尝试换一种描述方式")

    # 将检索结果映射回完整工具信息
    all_tools = await get_all_tools()

    # 测试时全部返回，实际部署时根据 results 过滤
    return ok(
        [
            {
                "name": t.name,
                "description": getattr(t, "description", ""),
                "parameters": getattr(t, "parameters", []),
            }
            for t in all_tools
        ],
        message=f"找到 {len(all_tools)} 个相关工具（共查询 top_n={top_n}），请根据工具名称和参数调用 execute_tool 来获取结果",
    )


@mcp.tool
async def execute_tool(req: ToolExecuteReqDTO) -> ResponseResult[ToolExecuteResDTO]:
    """
    按名称调用已注册的工程工具，并传入指定参数执行
    :param req: 包含工具名称 (name) 和调用参数 (arguments) 的请求体
    :return: 工具的执行结果
    """
    from app.mcp.tools.tools_mcp import mcp

    try:
        tool_result = await mcp.call_tool(req.name, req.arguments)
        return ok(ToolExecuteResDTO(name=req.name, result=tool_result))
    except Exception as e:
        return fail(f"工具 {req.name!r} 执行失败: {e}")


mcp_app = mcp.http_app(path="/mcp")
