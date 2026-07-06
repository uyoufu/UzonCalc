"""后处理器：按 ContextOptions.aliases 进行字符串替换"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base_post_handler import BasePostHandler
from .dom_utils import PostHandlerNode

if TYPE_CHECKING:
    from ...context import CalcContext


class SwapAlias(BasePostHandler):
    """后处理器：按 `ctx.options.aliases` 对字符串进行替换。

    说明：
    - 采用 dict 的插入顺序依次替换（Python 3.7+ 保序）
    - 仅替换 HTML 元素文本内容中的完整匹配，不修改标签名和属性
    - 当 `ctx` 或 `aliases` 为空时直接返回原字符串
    """

    priority = 10

    def handle(
        self, post_node: PostHandlerNode, ctx: Optional[CalcContext] = None
    ) -> None:
        if ctx is None:
            return

        aliases = ctx.options.aliases
        if not aliases:
            return

        # 过滤无效项：空 key、key/value 非字符串等
        replacements: dict[str, str] = {}
        for key, value in aliases.items():
            if value is None:
                continue
            if not isinstance(value, str):
                value = str(value)
            if key == value:
                continue
            replacements[key] = value

        if not replacements:
            return

        post_node.replace_text(lambda text: replacements.get(text, text))
        post_node.replace_tail(lambda text: replacements.get(text, text))
