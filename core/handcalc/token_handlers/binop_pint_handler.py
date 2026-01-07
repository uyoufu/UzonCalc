import ast
from typing import TYPE_CHECKING
from core.handcalc.formatters.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.base_token_handler import BaseTokenHandler

if TYPE_CHECKING:
    from core.handcalc.token_handlers.handlers_factory import (
        TokenHandlerFactory,
    )


class BinOpPintHandler(BaseTokenHandler):
    # 相较于默认的 BinOp 处理器，优先级更高
    order: int = 9900

    def __init__(self, handlers_factory: "TokenHandlerFactory") -> None:
        super().__init__(handlers_factory)

    def can_handle_core(self, ast_token: ast.BinOp) -> bool:
        # 仅处理 pint 相乘、相除、幂运算的情况
        handling_ops = (ast.Mult, ast.Div, ast.Pow)
        return isinstance(ast_token, ast.BinOp) and isinstance(
            ast_token.op, handling_ops
        )

    def handle(
        self, ast_token: ast.BinOp, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode | None:
        """
        处理单位的乘除幂运算
        其他情况交给默认的 BinOp 处理器处理
        """

        assert isinstance(ast_token, ast.BinOp)

        left_node = handlers.handle(ast_token.left)
        right_node = handlers.handle(ast_token.right)
        if left_node is None or right_node is None:
            return None

        # 只有以下情况才进行处理
        # 1. 值+单位
        # 2. 单位+单位
        # 3. 单位^值
        is_unit = self.is_unit(ast_token, left_node, right_node)
        if not is_unit:
            return None

        latex = ""
        substitution = ""
        start_unit = left_node.start_unit
        end_unit = right_node.end_unit

        # 皆为单位，使用完整表达式
        latex = r"{" + f"{ast.unparse(ast_token)}" + r"}"
        substitution = r"{" + f"{ast.unparse(ast_token)}" + r"}"

        # 相乘
        if isinstance(ast_token.op, ast.Mult) and not left_node.end_unit:
            # 前者非单位，使用空格相连
            latex = f"{left_node.expr} {right_node.expr}"
            substitution = f"{left_node.substitution} {right_node.substitution}"

        # 幂运算时，latex 使用 ^{{}} 形式
        if isinstance(ast_token.op, ast.Pow):
            end_unit = True

        return FormattedAstNode(
            targets=None,
            expr=latex,
            substitution=substitution,
            start_unit=start_unit,
            end_unit=end_unit,
        )

    def is_unit(
        self,
        ast_token: ast.BinOp,
        left_node: FormattedAstNode | None,
        right_node: FormattedAstNode | None,
    ) -> bool:
        # 只有以下情况才进行处理
        # 1. 值+单位
        # 2. 单位+单位
        # 3. 单位^值

        # 如果两者都不带单位，则交给默认处理器
        if left_node is None or right_node is None:
            self.ignore_tokens.add(ast_token)
            return False

        # case 1 和 case 2
        if right_node.start_unit:
            return True

        if left_node.end_unit and isinstance(ast_token.op, ast.Pow):
            return True

        self.ignore_tokens.add(ast_token)
        return False
