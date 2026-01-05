import ast
from typing import TYPE_CHECKING

from core.handcalc.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.base_token_handler import BaseTokenHandler
from core.handcalc.token_handlers.latex_utils import format_field_name_latex

if TYPE_CHECKING:
    from core.handcalc.token_handlers.handlers_factory import (
        TokenHandlerFactory,
    )


class NameStoreHandler(BaseTokenHandler):
    def can_handle_core(self, ast_token: ast.AST) -> bool:
        return isinstance(ast_token, ast.Name) and isinstance(ast_token.ctx, ast.Store)

    def handle(
        self, ast_token: ast.AST, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode:
        if isinstance(ast_token, ast.Name):
            target_name = ast_token.id
        else:
            target_name = "<complex_target>"

        return FormattedAstNode(
            targets=target_name,
            expr=handlers.formatter.format_variable(target_name),
            substitution=f"{target_name}",
        )
