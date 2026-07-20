"""Internal execution result exchanged by all sandbox backends."""

from typing import Any

from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    """Return one completed or input-waiting calculation step."""

    # 执行 ID
    # 每次执行都会生成唯一标识符
    executionId: str
    # 原始 HTML 内容，controller 返回前会清空，避免接口传输大块重复内容
    html: str
    isCompleted: bool = False
    # 收集的所有 UI windows
    # 格式为: [{"title": str, "fields": [{"name": str, "value": Any, "type": str, ...}], "caption": str}, ...]
    windows: list[dict[str, Any]] = Field(default_factory=list)
    # 模型设置，允许从属性中读取值
    model_config = {"from_attributes": True}
