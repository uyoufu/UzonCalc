import ast
from typing import TYPE_CHECKING
from core.handcalc.formatters.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.base_token_handler import BaseTokenHandler


if TYPE_CHECKING:
    from core.handcalc.token_handlers.handlers_factory import (
        TokenHandlerFactory,
    )


class AddOperatorHandler(BaseTokenHandler):
    # 是否是加法操作符
    def can_handle_core(self, ast_token: ast.operator):
        return isinstance(ast_token, (ast.Add, ast.UAdd))

    def handle(
        self, ast_token: ast.operator, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode:
        return FormattedAstNode(
            targets=None,
            expr="<mo>+</mo>",
            substitution="<mo>+</mo>",
        )


class SubOperatorHandler(BaseTokenHandler):
    # 是否是减法操作符
    def can_handle_core(self, ast_token: ast.operator):
        return isinstance(ast_token, (ast.Sub, ast.USub))

    def handle(
        self, ast_token: ast.operator, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode:
        return FormattedAstNode(
            targets=None,
            expr="<mo>-</mo>",
            substitution="<mo>-</mo>",
        )


class MultOperatorHandler(BaseTokenHandler):
    # 是否是乘法操作符
    def can_handle_core(self, ast_token: ast.operator):
        return isinstance(ast_token, ast.Mult)

    def handle(
        self, ast_token: ast.operator, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode:
        return FormattedAstNode(
            targets=None,
            expr=r"<mo>·</mo>",
            substitution=r"<mo>·</mo>",
        )


class DivOperatorHandler(BaseTokenHandler):
    # 是否是除法操作符
    def can_handle_core(self, ast_token: ast.operator):
        return isinstance(ast_token, ast.Div)

    def handle(
        self, ast_token: ast.operator, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode:
        # BinOpHandler 会对 ast.Div 做 \frac 特殊渲染；这里提供兜底符号。
        return FormattedAstNode(
            targets=None, expr="<mo>/</mo>", substitution="<mo>/</mo>"
        )


class FloorDivOperatorHandler(BaseTokenHandler):
    def can_handle_core(self, ast_token: ast.operator):
        return isinstance(ast_token, ast.FloorDiv)

    def handle(
        self, ast_token: ast.operator, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode:
        return FormattedAstNode(targets=None, expr="//", substitution="//")


class ModOperatorHandler(BaseTokenHandler):
    def can_handle_core(self, ast_token: ast.operator):
        return isinstance(ast_token, ast.Mod)

    def handle(
        self, ast_token: ast.operator, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode:
        return FormattedAstNode(
            targets=None, expr="<mo>%</mo>", substitution="<mo>%</mo>"
        )


# 矩阵乘法
class MatMultOperatorHandler(BaseTokenHandler):
    def can_handle_core(self, ast_token: ast.operator):
        return isinstance(ast_token, ast.MatMult)

    def handle(
        self, ast_token: ast.operator, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode:
        return FormattedAstNode(
            targets=None, expr="<mo>·</mo>", substitution="<mo>·</mo>"
        )


class PowOperatorHandler(BaseTokenHandler):
    def can_handle_core(self, ast_token: ast.operator):
        return isinstance(ast_token, ast.Pow)

    def handle(
        self, ast_token: ast.operator, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode:
        return FormattedAstNode(
            targets=None, expr="<mo>^</mo>", substitution="<mo>^</mo>"
        )
