import ast

from core.handcalc.field_names import FieldNames
from core.handcalc.recorders.base_recorder import BaseRecorder
from core.handcalc.token_handlers.latex_writer import LaTeXWriter


class ExprRecorder(BaseRecorder):
    def record(self, node: ast.Expr) -> ast.AST | list[ast.stmt]:
        # Skip instrumenter-inserted nodes or other explicitly skipped nodes.
        if getattr(node, FieldNames.skip_record, False):
            return node

        # Literal string statements (non-docstring) should be recorded as plain text.
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            record_call = ast.Expr(
                value=ast.Call(
                    func=ast.Name(id=FieldNames.uzon_record_step, ctx=ast.Load()),
                    args=[ast.Name(id=FieldNames.ctx, ctx=ast.Load())],
                    keywords=[
                        ast.keyword(arg="name", value=ast.Constant(value="")),
                        ast.keyword(
                            arg="expr", value=ast.Constant(value=node.value.value)
                        ),
                        ast.keyword(
                            arg="substitution",
                            value=ast.Constant(value=""),
                        ),
                        ast.keyword(
                            arg="locals_map",
                            value=ast.Call(
                                func=ast.Name(id="locals", ctx=ast.Load()),
                                args=[],
                                keywords=[],
                            ),
                        ),
                    ],
                )
            )
            ast.copy_location(record_call, node)
            return [node, record_call]

        # f-string expression statements: record the evaluated runtime string.
        if isinstance(node.value, ast.JoinedStr):
            record_call = ast.Expr(
                value=ast.Call(
                    func=ast.Name(id=FieldNames.uzon_record_step, ctx=ast.Load()),
                    args=[ast.Name(id=FieldNames.ctx, ctx=ast.Load())],
                    keywords=[
                        ast.keyword(arg="name", value=ast.Constant(value="")),
                        ast.keyword(arg="expr", value=node.value),
                        ast.keyword(
                            arg="substitution",
                            value=ast.Constant(value=""),
                        ),
                        ast.keyword(
                            arg="locals_map",
                            value=ast.Call(
                                func=ast.Name(id="locals", ctx=ast.Load()),
                                args=[],
                                keywords=[],
                            ),
                        ),
                    ],
                )
            )
            ast.copy_location(record_call, node)
            return [node, record_call]

        formatter = LaTeXWriter()
        result = formatter.format_expr(node.value)
        if result is None:
            return node

        # Expr statements don't have an assignment target; keep name empty.
        record_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id=FieldNames.uzon_record_step, ctx=ast.Load()),
                args=[ast.Name(id=FieldNames.ctx, ctx=ast.Load())],
                keywords=[
                    ast.keyword(arg="name", value=ast.Constant(value="")),
                    ast.keyword(arg="expr", value=ast.Constant(value=result.latex)),
                    ast.keyword(
                        arg="substitution",
                        value=ast.Constant(value=result.substitution),
                    ),
                    ast.keyword(
                        arg="locals_map",
                        value=ast.Call(
                            func=ast.Name(id="locals", ctx=ast.Load()),
                            args=[],
                            keywords=[],
                        ),
                    ),
                ],
            )
        )

        ast.copy_location(record_call, node)
        return [node, record_call]
