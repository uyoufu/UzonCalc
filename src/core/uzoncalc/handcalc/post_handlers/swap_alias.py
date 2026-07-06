"""后处理器：按 ContextOptions.aliases 进行字符串替换"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from lxml import etree

from .base_post_handler import BasePostHandler
from .dom_utils import replace_node_tail, replace_node_text

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

    def handle(self, node: etree._Element, ctx: Optional[CalcContext] = None) -> None:
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

        replace_node_text(node, lambda text: replacements.get(text, text))
        replace_node_tail(node, lambda text: replacements.get(text, text))
