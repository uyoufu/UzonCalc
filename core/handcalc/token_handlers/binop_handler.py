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

        def _unit_attr_name(node: ast.AST) -> str | None:
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "unit"
            ):
                return node.attr
            return None

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

        # pint: `10 * unit.meter` -> `10 meter` (avoid showing `unit` / UnitRegistry repr)
        if isinstance(ast_token.op, ast.Mult):
            left_unit = _unit_attr_name(ast_token.left)
            right_unit = _unit_attr_name(ast_token.right)
            if left_unit or right_unit:
                if left_unit and right_unit:
                    unit_expr = f"{left_unit} {right_unit}"
                    return FormattedAstNode(
                        targets=None, latex=unit_expr, substitution=unit_expr
                    )

                if right_unit:
                    return FormattedAstNode(
                        targets=None,
                        latex=f"{left_expr} {right_unit}",
                        substitution=f"{left_substitution} {right_unit}",
                    )

                # left_unit only
                return FormattedAstNode(
                    targets=None,
                    latex=f"{right_expr} {left_unit}",
                    substitution=f"{right_substitution} {left_unit}",
                )

        op_node = handlers.handle(ast_token.op)
        symbol = op_node.latex if op_node is not None else "?"

        return FormattedAstNode(
            targets=None,
            latex=f"{left_expr} {symbol} {right_expr}",
            substitution=f"{left_substitution} {symbol} {right_substitution}",
        )
