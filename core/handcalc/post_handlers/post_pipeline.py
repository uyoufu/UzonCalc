from typing import List
from core.handcalc.post_handlers.base_post_handler import BasePostHandler
from core.handcalc.post_handlers.parentheses_simplify import ParenthesesSimplify
from core.handcalc.post_handlers.swap_symbol import SwapSymbol


def get_default_post_handlers() -> List[BasePostHandler]:
    # 获取默认的后处理器列表
    return [
        ParenthesesSimplify(),
        SwapSymbol(),
    ]
