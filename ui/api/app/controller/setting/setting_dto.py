"""
用户设置相关的 DTO 定义
"""

from typing import Optional, Any
from app.controller.dto_base import BaseDTO


class UserSettingUpsertDTO(BaseDTO):
    """用户设置 Upsert 请求 DTO"""

    value: dict[str, Any]
    description: Optional[str] = None
