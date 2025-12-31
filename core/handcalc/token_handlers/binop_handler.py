import ast
from typing import TYPE_CHECKING

from core.handcalc.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.base_token_handler import BaseTokenHandler
from core.handcalc.token_handlers.latex_utils import (
    latex_group,
    needs_parens_in_binop,
    wrap_parens,
)

if TYPE_CHECKING:
    from core.handcalc.token_handlers.handlers_factory import (
        TokenHandlerFactory,
    )


class BinOpHandler(BaseTokenHandler):
    def can_handle_core(self, ast_token: ast.AST) -> bool:
        return isinstance(ast_token, ast.BinOp)

    def handle(
        self, ast_token: ast.AST, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode | None:
        assert isinstance(ast_token, ast.BinOp)

        left_node = handlers.handle(ast_token.left)
        right_node = handlers.handle(ast_token.right)
        if left_node is None or right_node is None:
            return None

        left_expr, left_substitution = left_node.latex, left_node.substitution
        right_expr, right_substitution = right_node.latex, right_node.substitution

        # 添加括号
        if needs_parens_in_binop(
            child=ast_token.left, parent_op=ast_token.op, side="left"
        ):
            left_expr = wrap_parens(left_expr)
            left_substitution = wrap_parens(left_substitution)
        if needs_parens_in_binop(
            child=ast_token.right, parent_op=ast_token.op, side="right"
        ):
            right_expr = wrap_parens(right_expr)
            right_substitution = wrap_parens(right_substitution)

        # Special LaTeX forms.
        if isinstance(ast_token.op, ast.Pow):
            return FormattedAstNode(
                targets=None,
                latex=f"{left_expr}^{latex_group(right_expr)}",
                substitution=f"{left_substitution}^{latex_group(right_substitution)}",
            )

        if isinstance(ast_token.op, ast.Div):
            return FormattedAstNode(
                targets=None,
                latex=f"\\frac{latex_group(left_expr)}{latex_group(right_expr)}",
                substitution=f"\\frac{latex_group(left_substitution)}{latex_group(right_substitution)}",
            )

        op_node = handlers.handle(ast_token.op)
        symbol = op_node.latex if op_node is not None else "?"

        return FormattedAstNode(
            targets=None,
            latex=f"{left_expr} {symbol} {right_expr}",
            substitution=f"{left_substitution} {symbol} {right_substitution}",
        )
