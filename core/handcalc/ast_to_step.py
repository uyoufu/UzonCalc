"""AST 到 Step IR 的转换器"""

import ast
from typing import Optional

from core.handcalc import ir
from core.handcalc import steps
from core.handcalc.ast_to_ir import expr_to_ir, target_to_ir


class AstToStepConverter:
    """将 AST 节点转换为 Step 对象"""

    @staticmethod
    def convert_assign(node: ast.Assign) -> steps.EquationStep:
        """转换赋值语句为 EquationStep"""
        if len(node.targets) == 1:
            lhs_ir = target_to_ir(node.targets[0])
        else:
            # Multi-target assignment: keep readable.
            try:
                lhs_ir = ir.mtext(", ".join(ast.unparse(t) for t in node.targets))
            except Exception:
                lhs_ir = ir.mtext("<targets>")

        rhs_ir = expr_to_ir(node.value)
        return steps.EquationStep(lhs=lhs_ir, rhs=rhs_ir)

    @staticmethod
    def convert_string_expr(text: str) -> steps.TextStep:
        """转换字符串字面量为 TextStep"""
        return steps.TextStep(text=text)

    @staticmethod
    def convert_expr(node: ast.expr) -> steps.ExprStep:
        """转换通用表达式为 ExprStep"""
        expr_ir = expr_to_ir(node)
        return steps.ExprStep(expr=expr_ir)

    @staticmethod
    def convert_name_expr(name: str) -> steps.EquationStep:
        """转换变量名表达式为 EquationStep"""
        return steps.EquationStep(lhs=ir.mi(name), rhs=None)

    @staticmethod
    def convert_fstring(
        node: ast.JoinedStr, value_vars: list[str] | None = None
    ) -> steps.FStringStep:
        """Convert an f-string AST node into a mixed text + formula step.

        value_vars: list of temp variable names capturing each FormattedValue's result.
        """
        value_vars = value_vars or []
        segments: list[steps.FStringSegment] = []
        value_idx = 0

        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                if v.value:
                    segments.append(steps.FStringSegment(kind="text", text=v.value))
                continue

            if isinstance(v, ast.FormattedValue):
                inner = v.value
                value_var = value_vars[value_idx] if value_idx < len(value_vars) else ""
                value_idx += 1

                # 提取格式化规范（如 .3f）
                format_spec = ""
                if v.format_spec and isinstance(v.format_spec, ast.JoinedStr):
                    # format_spec 是一个 JoinedStr，提取其文本内容
                    for spec_val in v.format_spec.values:
                        if isinstance(spec_val, ast.Constant) and isinstance(
                            spec_val.value, str
                        ):
                            format_spec += spec_val.value

                if isinstance(inner, ast.NamedExpr):
                    segments.append(
                        steps.FStringSegment(
                            kind="namedexpr",
                            lhs=target_to_ir(inner.target),
                            rhs=expr_to_ir(inner.value),
                            value_var=value_var,
                            format_spec=format_spec,
                        )
                    )
                else:
                    segments.append(
                        steps.FStringSegment(
                            kind="expr",
                            expr=expr_to_ir(inner),
                            value_var=value_var,
                            format_spec=format_spec,
                        )
                    )
                continue

            # Unknown segment types: keep readable.
            try:
                text = str(ast.unparse(v))
            except Exception:
                text = v.__class__.__name__
            segments.append(steps.FStringSegment(kind="text", text=text))

        return steps.FStringStep(segments=segments)
