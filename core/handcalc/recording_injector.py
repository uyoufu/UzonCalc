"""记录调用注入器 - 负责生成记录调用的 AST 代码"""

import ast
from typing import Optional

from core.handcalc import ir
from core.handcalc import steps
from core.handcalc.field_names import FieldNames


class RecordingInjector:
    """负责生成和注入记录调用的 AST 节点"""

    def make_record_call(
        self,
        original_node: ast.AST,
        *,
        step: steps.Step,
        value_node: Optional[ast.expr] = None,
        include_locals: bool = True,
    ) -> ast.Expr:
        """创建记录调用的 AST 表达式"""
        step_expr = self._step_to_ast(step)
        keywords: list[ast.keyword] = [
            ast.keyword(arg="step", value=step_expr),
        ]

        if include_locals:
            keywords.append(
                ast.keyword(
                    arg="locals_map",
                    value=ast.Call(
                        func=ast.Name(id="locals", ctx=ast.Load()),
                        args=[],
                        keywords=[],
                    ),
                )
            )

        if value_node is not None:
            keywords.append(ast.keyword(arg="value", value=value_node))

        record_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id=FieldNames.uzon_record_step, ctx=ast.Load()),
                args=[ast.Name(id=FieldNames.ctx, ctx=ast.Load())],
                keywords=keywords,
            )
        )
        ast.copy_location(record_call, original_node)
        return record_call

    def _step_to_ast(self, step: steps.Step) -> ast.expr:
        """将 Step 对象转换为构造它的 AST 表达式"""
        steps_mod = ast.Name(id=FieldNames.uzon_steps, ctx=ast.Load())

        if isinstance(step, steps.TextStep):
            ctor = ast.Attribute(value=steps_mod, attr="TextStep", ctx=ast.Load())
            return ast.Call(
                func=ctor,
                args=[],
                keywords=[ast.keyword(arg="text", value=ast.Constant(value=step.text))],
            )

        if isinstance(step, steps.ExprStep):
            ctor = ast.Attribute(value=steps_mod, attr="ExprStep", ctx=ast.Load())
            return ast.Call(
                func=ctor,
                args=[],
                keywords=[ast.keyword(arg="expr", value=self._value_to_ast(step.expr))],
            )

        if isinstance(step, steps.EquationStep):
            ctor = ast.Attribute(value=steps_mod, attr="EquationStep", ctx=ast.Load())
            return ast.Call(
                func=ctor,
                args=[],
                keywords=[
                    ast.keyword(arg="lhs", value=self._value_to_ast(step.lhs)),
                    ast.keyword(arg="rhs", value=self._value_to_ast(step.rhs)),
                ],
            )

        if isinstance(step, steps.FStringStep):
            ctor = ast.Attribute(value=steps_mod, attr="FStringStep", ctx=ast.Load())
            return ast.Call(
                func=ctor,
                args=[],
                keywords=[
                    ast.keyword(arg="segments", value=self._value_to_ast(step.segments)),
                ],
            )

        # Fallback: stringify step.
        ctor = ast.Attribute(value=steps_mod, attr="TextStep", ctx=ast.Load())
        return ast.Call(
            func=ctor,
            args=[],
            keywords=[ast.keyword(arg="text", value=ast.Constant(value=str(step)))],
        )

    def _value_to_ast(self, value: object) -> ast.expr:
        """将值转换为 AST 表达式"""
        if value is None or isinstance(value, (bool, int, float, str)):
            return ast.Constant(value=value)

        if isinstance(value, ir.MathNode):
            return self._math_to_ast(value)

        if isinstance(value, list):
            return ast.List(elts=[self._value_to_ast(v) for v in value], ctx=ast.Load())

        if isinstance(value, dict):
            keys: list[Optional[ast.expr]] = []
            values: list[ast.expr] = []
            for k, v in value.items():
                keys.append(ast.Constant(value=k))
                values.append(self._value_to_ast(v))
            return ast.Dict(keys=keys, values=values)

        return ast.Constant(value=str(value))

    def _math_to_ast(self, node: ir.MathNode | str) -> ast.expr:
        """将 MathNode 转换为 AST 表达式"""
        if isinstance(node, str):
            return ast.Constant(value=node)
        return node.to_python_ast(ir_var_name=FieldNames.uzon_ir)
