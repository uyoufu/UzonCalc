"""上下文结果后处理器管道。"""

from typing import List

from .base_context_result_handler import BaseContextResultHandler
from .toc import TocContextResultHandler


def get_default_context_result_handlers() -> List[BaseContextResultHandler]:
    """获取默认上下文结果后处理器。"""
    handlers: List[BaseContextResultHandler] = [
        TocContextResultHandler(),
    ]

    handlers.sort(key=lambda h: (getattr(h, "priority", 100), h.__class__.__name__))
    return handlers
