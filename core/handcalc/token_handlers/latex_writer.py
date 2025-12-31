import ast

from core.handcalc.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.handlers_factory import (
    TokenHandlerFactory,
)


class LaTeXWriter:
    def __init__(self, handlers: TokenHandlerFactory | None = None):
        self._handlers = handlers or TokenHandlerFactory()

    # 格式化赋值语句
    def format_assign(self, node: ast.Assign) -> FormattedAstNode | None:
        if not node.targets:
            return None

        first_target = node.targets[0]
        target_node = self._handlers.handle(first_target)
        value_node = self._handlers.handle(node.value)

        if target_node is None or value_node is None:
            return None

        return FormattedAstNode(
            targets=target_node.latex,
            latex=value_node.latex,
            substitution=value_node.substitution,
        )

    def format_expr(self, node: ast.expr) -> FormattedAstNode | None:
        return self._handlers.handle(node)
