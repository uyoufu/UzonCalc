import ast
from typing import TYPE_CHECKING
from core.handcalc.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.base_token_handler import BaseTokenHandler


if TYPE_CHECKING:
    from core.handcalc.token_handlers.handlers_factory import (
        TokenHandlerFactory,
    )


class AssignHandler(BaseTokenHandler):
    def can_handle_core(self, ast_token: ast.Assign) -> bool:
        return isinstance(ast_token, ast.Assign)

    def handle(
        self, ast_token: ast.Assign, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode | None:
        """
        处理赋值语句

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
        target_node = handlers.handle(first_target)

        # 处理右侧表达式
        value_node = handlers.handle(ast_token.value)

        # 组合成最终的赋值表达式
        if target_node and value_node:
            latex = f"{target_node.latex} = {value_node.latex}"
            substitution = f"{target_node.substitution} = {value_node.substitution}"
            return FormattedAstNode(
                targets=target_node.targets,
                latex=latex,
                substitution=substitution,
            )
