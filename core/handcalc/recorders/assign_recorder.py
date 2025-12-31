import ast
from core.handcalc.field_names import FieldNames
from core.handcalc.token_handlers.latex_writer import LaTeXWriter
from core.handcalc.recorders.base_recorder import BaseRecorder, RecordedNode


class AssignRecorder(BaseRecorder):

    def record(self, node: ast.Assign) -> ast.AST:
        """
        将赋值语句转换手写公式
        """

        # 跳过时，不处理
        if getattr(node, FieldNames.skip_record, False):
            return node

        # TODO: 多目标赋值处理
        # 仅处理单目标赋值
        if len(node.targets) != 1:
            return node

        # 仅处理简单变量名赋值, a = xxx 形式
        # 暂不处理元组、列表解包
        # 属性赋值
        # 下标赋值
        # 带*的解包
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            return node

        # 私有变量（以 _ 开头）可在运行时根据 ctx.options 决定是否抑制；
        # 这里依旧插入记录调用，避免静态决定导致行为不一致。

        formatter = LaTeXWriter()
        result = formatter.format_assign(node)
        if result is None:
            return node

        record_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id=FieldNames.uzon_record_step, ctx=ast.Load()),
                args=[ast.Name(id=FieldNames.ctx, ctx=ast.Load())],
                keywords=[
                    ast.keyword(
                        arg="name",
                        value=ast.Constant(value=result.targets or target.id),
                    ),
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
                    # ast.keyword(arg="is_expr_stmt", value=ast.Constant(value=False)),
                ],
            )
        )

        ast.copy_location(record_call, node)
        return [node, record_call]
