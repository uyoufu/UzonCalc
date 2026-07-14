# 仅为 pylance 提供类型提示，实际运行时不会导入 FastMCPComponent
from typing import TYPE_CHECKING, Sequence

from fastmcp.tools import Tool

# 在此处加载所有的 tools
import app.mcp.tools.jtgb01_2014.core


async def get_all_tools() -> Sequence[Tool]:
    from .tools_mcp import mcp

    return await mcp.list_tools()
