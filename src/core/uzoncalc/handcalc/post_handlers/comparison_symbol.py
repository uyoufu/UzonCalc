"""后处理器：将比较运算文本替换为数学比较符号。"""

from __future__ import annotations

from lxml import etree

from .base_post_handler import BasePostHandler
from .dom_utils import replace_node_tail, replace_node_text


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

    def handle(self, node: etree._Element, ctx=None) -> None:
        """转换当前节点可见文本中的比较运算符。"""
        replace_node_text(
            node, self._replace_comparison_symbols, skip_tags=self._SKIP_TEXT_TAGS
        )
        replace_node_tail(
            node, self._replace_comparison_symbols, skip_tags=self._SKIP_TEXT_TAGS
        )

    def _replace_comparison_symbols(self, text: str) -> str:
        """转换普通文本中的比较运算符。"""
        for source, target in self._REPLACEMENTS.items():
            text = text.replace(source, target)
        return text
