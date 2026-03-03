from typing import Any

from fastmcp import FastMCP
from fastapi import FastAPI, APIRouter, Query

from pydantic import BaseModel, Field

from app.mcp.mcp_dto import (
    ToolExecuteReqDTO,
    ToolExecuteResDTO,
    ToolInfoDTO,
    ToolListResDTO,
)
from app.response.response_result import ResponseResult, ok, fail

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "Engineering MCP",
    version="1.0",
    instructions="该 MCP 主要用于工程相关的任务，如代规范参数查询、受力计算、结构分析等",
)


# 加载所有的工具函数，方便进行查询检索
import app.mcp.tools

# 将 MCP 保存到数据库中


@mcp.tool
async def query_tool(
    category: str = Query(..., description="工具类别"),
    name: str = Query(..., description="工具名称"),
) -> ResponseResult[ToolInfoDTO]:
    """
    查询工具信息
    :param category: 工具类别
    :param name: 工具名称
    :return: 工具信息
    """


@mcp.tool
async def execute_tool(req: ToolExecuteReqDTO) -> ToolExecuteResDTO:
    """
    这是一个示例工具函数，用于执行具体的工具操作。
    实际应用中可以根据需要实现更复杂的逻辑。
    """


mcp_app = mcp.http_app(path="/mcp")
