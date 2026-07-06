from .base_post_handler import BasePostHandler
import re
from lxml import etree

from .dom_utils import element_tag_name


class ParenthesesSimplify(BasePostHandler):
    """
    当存在 (纯简单数值) 时，去掉括号
    仅处理 MathML 标签内的数字，不影响普通文本内容
    """

    priority = 40

    def handle(self, node: etree._Element, ctx=None) -> None:
        # 只匹配 MathML 数字标签 <mn> 内的括号数字
        # 例如: <mn>(5)</mn> -> <mn>5</mn>
        if element_tag_name(node) != "mn" or node.text is None:
            return
        node.text = re.sub(r"^\(\s*(\d+(?:\.\d+)?)\s*\)$", r"\1", node.text)
