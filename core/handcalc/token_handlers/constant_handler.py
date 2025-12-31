import ast
from typing import TYPE_CHECKING

from core.handcalc.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.base_token_handler import BaseTokenHandler
from core.handcalc.token_handlers.latex_utils import latex_literal

if TYPE_CHECKING:
    from core.handcalc.token_handlers.handlers_factory import (
        TokenHandlerFactory,
    )


class ConstantHandler(BaseTokenHandler):
    def can_handle_core(self, ast_token: ast.AST) -> bool:
        return isinstance(ast_token, ast.Constant)

    def handle(
        self, ast_token: ast.AST, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode:
        assert isinstance(ast_token, ast.Constant)

        v = ast_token.value
        if isinstance(v, str):
            s = repr(v)
        elif v is None:
            s = "None"
        elif v is True:
            s = "True"
        elif v is False:
            s = "False"
        else:
            s = str(v)

        lit = latex_literal(s)
        return FormattedAstNode(targets=None, latex=lit, substitution=lit)
