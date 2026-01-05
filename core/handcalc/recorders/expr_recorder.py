import ast

from core.handcalc.field_names import FieldNames
from core.handcalc.recorders.base_recorder import BaseRecorder
from core.handcalc.token_handlers.handlers_factory import TokenHandlerFactory


class ExprRecorder(BaseRecorder):
    def __init__(self, handlersFactory: TokenHandlerFactory) -> None:
        super().__init__()
        self._handlers = handlersFactory

    def record(self, node: ast.Expr) -> ast.AST | list[ast.stmt]:
        # 跳过不记录的节点
        if getattr(node, FieldNames.skip_record, False):
            return node

        # 忽略函数调用表达式
        if isinstance(node.value, ast.Call):
            return node

        # 形如：
        # b
        # 的表达式语句（ast.Expr(value=ast.Name)），希望渲染为：b = <value>
        # 通过把 name 设为变量名、并传入运行时 value 来实现。
        if isinstance(node.value, ast.Name) and isinstance(node.value.ctx, ast.Load):
            record_call = ast.Expr(
                value=ast.Call(
                    func=ast.Name(id=FieldNames.uzon_record_step, ctx=ast.Load()),
                    args=[ast.Name(id=FieldNames.ctx, ctx=ast.Load())],
                    keywords=[
                        ast.keyword(
                            arg="name", value=ast.Constant(value=node.value.id)
                        ),
                        ast.keyword(arg="expr", value=ast.Constant(value="")),
                        ast.keyword(
                            arg="substitution",
                            value=ast.Constant(value=""),
                        ),
                        ast.keyword(
                            arg="value",
                            value=ast.Name(id=node.value.id, ctx=ast.Load()),
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

        # 其它表达式，使用 LaTeX 格式化
        result = self._handlers.handle(node)
        if result is None:
            return node

        # Expr statements don't have an assignment target; keep name empty.
        record_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id=FieldNames.uzon_record_step, ctx=ast.Load()),
                args=[ast.Name(id=FieldNames.ctx, ctx=ast.Load())],
                keywords=[
                    ast.keyword(arg="name", value=ast.Constant(value="")),
                    ast.keyword(arg="expr", value=ast.Constant(value=result.expr)),
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
