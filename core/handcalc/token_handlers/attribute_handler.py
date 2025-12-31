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

        base_node = handlers.handle(ast_token.value)
        if base_node is None:
            return None

        base_expr = base_node.latex
        base_substitution = base_node.substitution

        if isinstance(ast_token.value, ast.BinOp):
            base_expr = wrap_parens(base_expr)
            base_substitution = wrap_parens(base_substitution)

        # 生成 LaTeX 表达式
        # 示例：{obj.attr}
        substitution = r"{" + f"{ast_token.value.id}.{ast_token.attr}" + r"}"

        # 判断是否有单位关键字
        with_unit = ast_token.value.id == FieldNames.unit

        return FormattedAstNode(
            targets=None,
            latex=substitution,
            substitution=substitution,
            start_unit=with_unit,
            end_unit=with_unit,
        )
