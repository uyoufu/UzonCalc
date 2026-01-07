import ast
from typing import TYPE_CHECKING

from core.handcalc.formatters.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.base_token_handler import BaseTokenHandler


if TYPE_CHECKING:
    from core.handcalc.token_handlers.handlers_factory import (
        TokenHandlerFactory,
    )


class CallHandler(BaseTokenHandler):
    def can_handle_core(self, ast_token: ast.AST) -> bool:
        return isinstance(ast_token, ast.Call)

    def handle(
        self, ast_token: ast.AST, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode | None:
        assert isinstance(ast_token, ast.Call)

        # Special-case absolute value: abs(x) -> |x|
        # Keep this intentionally narrow to the builtin `abs` with one positional arg.
        if (
            isinstance(ast_token.func, ast.Name)
            and ast_token.func.id == "abs"
            and len(ast_token.args) == 1
            and len(ast_token.keywords) == 0
        ):
            n = handlers.handle(ast_token.args[0])
            if n is None:
                return None
            return FormattedAstNode(
                targets=None,
                expr=handlers.formatter.format_abs(n.expr),
                substitution=handlers.formatter.format_abs(n.substitution),
            )

        # Keep function name literal when it is a simple Name.
        if isinstance(ast_token.func, ast.Name):
            func_expr = ast_token.func.id
            func_tmpl = ast_token.func.id
        else:
            func_node = handlers.handle(ast_token.func)
            if func_node is None:
                return None
            func_expr = func_node.expr
            func_tmpl = func_node.substitution

        arg_exprs: list[str] = []
        arg_tmpls: list[str] = []

        for a in ast_token.args:
            n = handlers.handle(a)
            if n is None:
                return None
            arg_exprs.append(n.expr)
            arg_tmpls.append(n.substitution)

        for kw in ast_token.keywords:
            n = handlers.handle(kw.value)
            if n is None:
                return None
            if kw.arg is None:
                arg_exprs.append(f"**{n.expr}")
                arg_tmpls.append(f"**{n.substitution}")
            else:
                arg_exprs.append(f"{kw.arg}={n.expr}")
                arg_tmpls.append(f"{kw.arg}={n.substitution}")

        return FormattedAstNode(
            targets=None,
            expr=f"{func_expr}({', '.join(arg_exprs)})",
            substitution=f"{func_tmpl}({', '.join(arg_tmpls)})",
        )
