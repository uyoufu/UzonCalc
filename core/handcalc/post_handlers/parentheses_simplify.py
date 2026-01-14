from core.handcalc.post_handlers.base_post_handler import BasePostHandler
import re


class ParenthesesSimplify(BasePostHandler):
    """
    当存在 (纯简单数值) 时，去掉括号
    仅处理 MathML 标签内的数字，不影响普通文本内容
    """

    def handle(self, data: str) -> str:
        # 只匹配 MathML 数字标签 <mn> 内的括号数字
        # 例如: <mn>(5)</mn> -> <mn>5</mn>
        # 但不会影响 <p>(2) 中央防撞护栏：</p> 这样的文本内容
        pattern = r"<mn>\(\s*(\d+(?:\.\d+)?)\s*\)</mn>"
        simplified_data = re.sub(pattern, r"<mn>\1</mn>", data)
        return simplified_data
