import ast
from typing import TYPE_CHECKING

from core.handcalc.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.base_token_handler import BaseTokenHandler
from core.handcalc.token_handlers.latex_utils import precedence, wrap_parens

if TYPE_CHECKING:
    from core.handcalc.token_handlers.handlers_factory import (
        TokenHandlerFactory,
    )


class UnaryOpHandler(BaseTokenHandler):
    def can_handle_core(self, ast_token: ast.AST) -> bool:
        return isinstance(ast_token, ast.UnaryOp)

    def _op(self, op: ast.unaryop) -> str:
        if isinstance(op, ast.UAdd):
            return "+"
        if isinstance(op, ast.USub):
            return "-"
        if isinstance(op, ast.Not):
            return r"\lnot "
        if isinstance(op, ast.Invert):
            return r"\sim "
        return ""

    def handle(
        self, ast_token: ast.AST, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode | None:
        assert isinstance(ast_token, ast.UnaryOp)

        op = self._op(ast_token.op)
        operand_node = handlers.handle(ast_token.operand)
        if operand_node is None:
            return None

        operand_expr = operand_node.expr
        operand_tmpl = operand_node.substitution

        if isinstance(ast_token.operand, ast.BinOp) and precedence(
            ast_token.operand
        ) < precedence(ast_token):
            operand_expr = wrap_parens(operand_expr)
            operand_tmpl = wrap_parens(operand_tmpl)

        return FormattedAstNode(
            targets=None,
            expr=f"{op}{operand_expr}",
            substitution=f"{op}{operand_tmpl}",
        )
