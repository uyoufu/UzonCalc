import ast
from typing import TYPE_CHECKING
from core.handcalc.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.base_token_handler import BaseTokenHandler

if TYPE_CHECKING:
    from core.handcalc.token_handlers.handlers_factory import (
        TokenHandlerFactory,
    )


class BinOpPintHandler(BaseTokenHandler):
    # 相较于默认的 BinOp 处理器，优先级更高
    order: int = 9900

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
        处理单位乘除的情况，如:
            length = 5 * u.m -> length = 5 \\mathrm{m}
            speed = 10 * u.m / u.s -> speed = 10 \\mathrm{m/s}
            compress = 1 * u.N / u.m**2 -> compress = 1 \\mathrm{N/m^{2}}
        仅处理涉及 pint 单位的乘除法
        其他情况交给默认的 BinOp 处理器处理
        """

        assert isinstance(ast_token, ast.BinOp)

        left_node = handlers.handle(ast_token.left)
        right_node = handlers.handle(ast_token.right)

        # 如果两者都不带单位，则交给默认处理器
        if left_node is None or right_node is None:
            self.ignore_tokens.add(ast_token)
            return None

        # 若两者都不是单位，则交给默认处理器
        if not left_node.start_unit and not right_node.start_unit:
            self.ignore_tokens.add(ast_token)
            return None

        # 若后者不是单位且非 pow 情况，则交给默认处理器
        if not right_node.start_unit and not isinstance(ast_token.op, ast.Pow):
            self.ignore_tokens.add(ast_token)
            return None

        latex = ""
        substitution = ""
        start_unit = left_node.start_unit
        end_unit = right_node.end_unit

        # 相乘时，前者非单位时，直接相连
        if isinstance(ast_token.op, ast.Mult):
            if not left_node.end_unit:
                latex = f"{left_node.latex} {right_node.latex}"
                substitution = f"{left_node.substitution} {right_node.substitution}"
            else:
                latex = f"{left_node.latex} \\cdot {right_node.latex}"
                substitution = (
                    f"{left_node.substitution} \\cdot {right_node.substitution}"
                )

        # 相除时，使用 / 符号连接
        elif isinstance(ast_token.op, ast.Div):
            latex = f"{left_node.latex}/{right_node.latex}"
            substitution = f"{left_node.substitution} / {right_node.substitution}"

        # 幂运算时，latex 使用 ^{{}} 形式
        elif isinstance(ast_token.op, ast.Pow):
            latex = f"{left_node.latex} ^" + r"{{" + right_node.latex + r"}}"
            substitution = (
                f"{left_node.substitution}^" + r"{{" + right_node.substitution + r"}}"
            )
            end_unit = True

        return FormattedAstNode(
            targets=None,
            latex=latex,
            substitution=substitution,
            start_unit=start_unit,
            end_unit=end_unit,
        )
