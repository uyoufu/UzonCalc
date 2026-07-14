"""
MCP (Model Context Protocol) DTO 定义
规范版本: 2025-06-18
参考: https://modelcontextprotocol.io/specification/2025-06-18
"""

from typing import Any, Literal

from pydantic import Field

from app.controller.dto_base import BaseDTO


class ToolExecuteReqDTO(BaseDTO):
    name: str = Field(..., description="要调用的工具名称")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="传递给工具的参数，键值对形式"
    )


class ToolExecuteResDTO(BaseDTO):
    name: str = Field(..., description="被调用的工具名称")
    result: Any = Field(..., description="工具执行的结构化返回值")
