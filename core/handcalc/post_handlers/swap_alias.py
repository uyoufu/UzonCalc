"""后处理器：按 ContextOptions.aliases 进行字符串替换"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from core.handcalc.post_handlers.base_post_handler import BasePostHandler

if TYPE_CHECKING:
    from core.context import CalcContext


class SwapAlias(BasePostHandler):
    """后处理器：按 `ctx.options.aliases` 对字符串进行替换。

    说明：
    - 采用 dict 的插入顺序依次替换（Python 3.7+ 保序）
    - 当 `ctx` 或 `aliases` 为空时直接返回原字符串
    """

    priority = 10

    def handle(self, data: str, ctx: Optional[CalcContext] = None) -> str:
        if ctx is None:
            return data

        aliases = ctx.options.aliases
        if not aliases:
            return data

        # 过滤无效项：空 key、key/value 非字符串等
        replacements: list[tuple[str, str]] = []
        for key, value in aliases.items():
            if value is None:
                continue
            if not isinstance(value, str):
                value = str(value)
            if key == value:
                continue
            replacements.append((key, value))

        if not replacements:
            return data
  
        for key, value in replacements:
            data = data.replace(key, value)

        return data
