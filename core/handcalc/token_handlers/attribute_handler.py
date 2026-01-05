import ast
from typing import TYPE_CHECKING

from core.handcalc.field_names import FieldNames
from core.handcalc.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.base_token_handler import BaseTokenHandler
from core.handcalc.token_handlers.latex_utils import wrap_parens

if TYPE_CHECKING:
    from core.handcalc.token_handlers.handlers_factory import (
        TokenHandlerFactory,
    )


class AttributeHandler(BaseTokenHandler):
    def can_handle_core(self, ast_token: ast.AST) -> bool:
        return isinstance(ast_token, ast.Attribute)

    def handle(
        self, ast_token: ast.AST, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode | None:
        """
        处理属性访问，如 obj.attr
        """
        assert isinstance(ast_token, ast.Attribute)

        # 判断是否有单位关键字
        is_unit = ast_token.value.id == FieldNames.unit
        substitution = r"{" + f"{ast_token.value.id}.{ast_token.attr}" + r"}"
        base_expr = substitution

        return FormattedAstNode(
            targets=None,
            expr=base_expr,
            substitution=substitution,
            start_unit=is_unit,
            end_unit=is_unit,
            contains_variable=not is_unit,
        )
