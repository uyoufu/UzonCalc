import ast
from typing import TYPE_CHECKING, Any
from core.handcalc.formatters.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.base_token_handler import BaseTokenHandler


if TYPE_CHECKING:
    from core.handcalc.token_handlers.handlers_factory import (
        TokenHandlerFactory,
    )


class AssignHandler(BaseTokenHandler):
    def __init__(self, handlers_factory: "TokenHandlerFactory") -> None:
        super().__init__(handlers_factory)

    def can_handle_core(self, ast_token: ast.Assign, parent: Any | None = None) -> bool:
        return isinstance(ast_token, ast.Assign)

    def handle(
        self,
        ast_token: ast.Assign,
        parent: FormattedAstNode | None = None,
    ) -> FormattedAstNode | None:
        """
        处理赋值语句, 有以下情况：
        1. 简单变量赋值，如：x = 5 + 3
        2. 多目标赋值，如：a = b = 10
        3. 解包赋值，如：x, y = (1, 2)
        4. 属性赋值，如：obj.attr = value
        5. 下标赋值，如：arr[0] = value
        6. 带*的解包赋值，如：a, *b = [1, 2, 3, 4]
        7. 增强赋值，如：x += 5 （暂不处理）

        当表达式中仅包含 + 时，可能为字符串拼接

        :param self: 说明
        :param ast_token: 说明
        :type ast_token: ast.Assign
        :param handlers: 说明
        :type handlers: "TokenHandlerFactory"
        :return: 说明
        :rtype: FormattedAstNode | None
        """

        # 处理左侧目标
        first_target = ast_token.targets[0]
        target_node = self.handlers_factory.handle(first_target)

        # 处理右侧表达式
        value_node = self.handlers_factory.handle(ast_token.value)

        # 组合成最终的赋值表达式
        if target_node and value_node:
            latex = f"{target_node.expr} = {value_node.expr}"
            substitution = f"{target_node.substitution} = {value_node.substitution}"
            return FormattedAstNode(
                targets=target_node.targets,
                expr=latex,
                substitution=substitution,
            )
