from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ExecutionResult(BaseModel):
    # 执行 ID
    # 每次执行都会生成唯一标识符
    executionId: str
    # 原始 HTML 内容，controller 返回前会清空，避免接口传输大块重复内容
    html: str
    # 缓存后的 HTML 相对路径
    htmlPath: str = ""
    isCompleted: bool = False
    # 收集的所有 UI windows
    # 格式为: [{"title": str, "fields": [{"name": str, "value": Any, "type": str, ...}], "caption": str}, ...]
    windows: List[Dict[str, Any]] = []
    # HTML 正文增量补丁，存在时前端可复用当前 iframe
    htmlContentPatch: Optional[str] = None
    model_config = {"from_attributes": True}
