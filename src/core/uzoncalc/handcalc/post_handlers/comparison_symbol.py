"""后处理器：将比较运算文本替换为数学比较符号。"""

from __future__ import annotations

from .base_post_handler import BasePostHandler
from .dom_utils import PostHandlerNode


class ComparisonSymbol(BasePostHandler):
    """后处理器：将可见文本中的比较运算符替换为数学符号。"""

    priority = 20

    _REPLACEMENTS = {
        "<=": "≤",
        ">=": "≥",
        "!=": "≠",
        "==": "≡",
    }
    _SKIP_TEXT_TAGS = {"code", "pre", "script", "style", "latex"}

    def handle(self, post_node: PostHandlerNode, ctx=None) -> None:
        """转换当前节点可见文本中的比较运算符。"""
        post_node.replace_text(
            self._replace_comparison_symbols, skip_tags=self._SKIP_TEXT_TAGS
        )
        post_node.replace_tail(
            self._replace_comparison_symbols, skip_tags=self._SKIP_TEXT_TAGS
        )

    def _replace_comparison_symbols(self, text: str) -> str:
        """转换普通文本中的比较运算符。"""
        for source, target in self._REPLACEMENTS.items():
            text = text.replace(source, target)
        return text
