"""记录调用注入器 - 负责生成记录调用的 AST 代码"""

import ast
from typing import Optional

from . import ir
from . import steps
from .field_names import FieldNames


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
                args=[],
                keywords=keywords,
            )
        )
        ast.copy_location(record_call, original_node)
        return record_call

    def _step_to_ast(self, step: steps.Step) -> ast.expr:
        """将 Step 对象转换为构造它的 AST 表达式"""
        steps_mod = ast.Name(id=FieldNames.uzon_steps, ctx=ast.Load())

        # 映射表: (class_name, kwargs_builder)
        type_map = {
            steps.TextStep: ("TextStep", lambda s: [("text", s.text)]),
            steps.ExprStep: ("ExprStep", lambda s: [("expr", s.expr)]),
            steps.EquationStep: (
                "EquationStep",
                lambda s: [("lhs", s.lhs), ("rhs", s.rhs)],
            ),
            steps.FStringStep: ("FStringStep", lambda s: [("segments", s.segments)]),
        }

        step_type = type(step)
        if step_type in type_map:
            class_name, kwargs_builder = type_map[step_type]
            ctor = ast.Attribute(value=steps_mod, attr=class_name, ctx=ast.Load())
            keywords = [
                ast.keyword(arg=k, value=self._value_to_ast(v))
                for k, v in kwargs_builder(step)
            ]
            return ast.Call(func=ctor, args=[], keywords=keywords)

        # Fallback: stringify step
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

        if isinstance(value, steps.FStringSegment):
            return self._fstring_segment_to_ast(value)

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

    def _fstring_segment_to_ast(self, segment: steps.FStringSegment) -> ast.expr:
        """将 FStringSegment 转换为 AST 表达式"""
        steps_mod = ast.Name(id=FieldNames.uzon_steps, ctx=ast.Load())
        ctor = ast.Attribute(value=steps_mod, attr="FStringSegment", ctx=ast.Load())

        keywords = [ast.keyword(arg="kind", value=ast.Constant(value=segment.kind))]

        if segment.kind == "text":
            keywords.append(
                ast.keyword(arg="text", value=ast.Constant(value=segment.text))
            )
        elif segment.kind == "expr":
            if segment.expr is not None:
                keywords.append(
                    ast.keyword(arg="expr", value=self._math_to_ast(segment.expr))
                )
            if segment.value_var:
                keywords.append(
                    ast.keyword(
                        arg="value_var", value=ast.Constant(value=segment.value_var)
                    )
                )
            if segment.format_spec:
                keywords.append(
                    ast.keyword(
                        arg="format_spec", value=ast.Constant(value=segment.format_spec)
                    )
                )
        elif segment.kind == "namedexpr":
            if segment.lhs is not None:
                keywords.append(
                    ast.keyword(arg="lhs", value=self._math_to_ast(segment.lhs))
                )
            if segment.rhs is not None:
                keywords.append(
                    ast.keyword(arg="rhs", value=self._math_to_ast(segment.rhs))
                )
            if segment.value_var:
                keywords.append(
                    ast.keyword(
                        arg="value_var", value=ast.Constant(value=segment.value_var)
                    )
                )
            if segment.format_spec:
                keywords.append(
                    ast.keyword(
                        arg="format_spec", value=ast.Constant(value=segment.format_spec)
                    )
                )

        return ast.Call(func=ctor, args=[], keywords=keywords)
