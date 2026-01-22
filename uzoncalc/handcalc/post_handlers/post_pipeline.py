"""后处理器管道 - 手动导入处理器"""

from typing import List
from .base_post_handler import BasePostHandler
from .parentheses_simplify import ParenthesesSimplify
from .swap_symbol import SwapSymbol
from .swap_alias import SwapAlias
from .subscriptify import Subscriptify


def get_default_post_handlers() -> List[BasePostHandler]:
    """获取所有后处理器

    按优先级执行（数值越小越靠前），同优先级按类名稳定排序
    """
    handlers: List[BasePostHandler] = [
        ParenthesesSimplify(),
        SwapSymbol(),
        SwapAlias(),
        Subscriptify(),
    ]

    # 按优先级排序（数值越小越靠前），同优先级按类名稳定排序
    handlers.sort(key=lambda h: (getattr(h, "priority", 100), h.__class__.__name__))
    return handlers
