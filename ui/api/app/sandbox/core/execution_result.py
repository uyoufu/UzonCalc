from pydantic import BaseModel
from typing import List, Dict, Any


class ExecutionResult(BaseModel):
    executionId: str
    html: str
    isCompleted: bool = False
    # 收集的所有 UI windows
    # 格式为: [{"title": str, "fields": [{"name": str, "value": Any, "type": str, ...}], "caption": str}, ...]
    windows: List[Dict[str, Any]] = []
    model_config = {"from_attributes": True}
