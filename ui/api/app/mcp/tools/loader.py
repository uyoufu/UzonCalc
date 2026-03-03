# 仅为 pylance 提供类型提示，实际运行时不会导入 FastMCPComponent
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from fastmcp.utilities.components import FastMCPComponent

# 在此处加载所有的 tools
import app.mcp.tools.jtgb01_2014.core


def get_all_tools() -> dict[str, FastMCPComponent]:
    from .tools_mcp import mcp

    return mcp.local_provider._components
