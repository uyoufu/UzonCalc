import ast
from typing import TYPE_CHECKING

from core.handcalc.formatters.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.base_token_handler import BaseTokenHandler
from core.handcalc.token_handlers.token_utils import latex_literal

if TYPE_CHECKING:
    from core.handcalc.token_handlers.handlers_factory import (
        TokenHandlerFactory,
    )


class ConstantHandler(BaseTokenHandler):
    def __init__(self, handlers_factory: "TokenHandlerFactory") -> None:
        super().__init__(handlers_factory)

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

        mathml_s = "<mn>" + s + "</mn>"
        return FormattedAstNode(targets=None, expr=mathml_s, substitution=mathml_s)
