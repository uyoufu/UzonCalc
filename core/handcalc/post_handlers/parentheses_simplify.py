from core.handcalc.post_handlers.base_post_handler import BasePostHandler
import re


class ParenthesesSimplify(BasePostHandler):
    """
    当存在 (纯简单数值) 时，去掉括号
    """

    def handle(self, data: str) -> str:
        pattern = r"\(\s*(\d+(\.\d+)?)\s*\)"
        simplified_data = re.sub(pattern, r"\1", data)
        return simplified_data
