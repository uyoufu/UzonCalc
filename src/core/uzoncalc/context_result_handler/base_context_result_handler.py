from __future__ import annotations

from abc import ABC, abstractmethod
from ..handler_protocols import HandlerContext


class BaseContextResultHandler(ABC):
    """上下文结果后处理器基类。"""

    priority: int = 100

    @abstractmethod
    def handle(self, html: str, ctx: HandlerContext | None = None) -> str:
        """处理完整 HTML 正文片段。"""
