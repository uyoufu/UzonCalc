import ast
from core.handcalc.field_names import FieldNames
from core.handcalc.formatted_ast_node import FormattedAstNode
from core.handcalc.token_handlers.handlers_factory import TokenHandlerFactory
from core.handcalc.recorders.base_recorder import BaseRecorder


class AssignRecorder(BaseRecorder):
    def __init__(self, handlersFactory: TokenHandlerFactory) -> None:
        super().__init__()
        self._handlers = handlersFactory

    def record(self, node: ast.Assign) -> ast.AST | list[ast.stmt]:
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
        first_target = node.targets[0]
        if not isinstance(first_target, ast.Name):
            return node

        # 私有变量（以 _ 开头）可在运行时根据 ctx.options 决定是否抑制；
        # 这里依旧插入记录调用，避免静态决定导致行为不一致。
        result = self.format_assign(node)
        if result is None:
            return node

        # 提取 expr 和 substitution 中的表达式，然后注入临时变量，再替换为变量名
        (result, assigns) = self.inject_temp_var(node, result)

        record_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id=FieldNames.uzon_record_step, ctx=ast.Load()),
                args=[ast.Name(id=FieldNames.ctx, ctx=ast.Load())],
                keywords=[
                    ast.keyword(
                        arg="name",
                        value=ast.Constant(value=result.targets or first_target.id),
                    ),
                    ast.keyword(arg="expr", value=ast.Constant(value=result.expr)),
                    ast.keyword(
                        arg="substitution",
                        value=ast.Constant(value=result.substitution),
                    ),
                    # 新增：传入变量的运行时值
                    ast.keyword(
                        arg="value",
                        value=ast.Name(id=first_target.id, ctx=ast.Load()),
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
        return [node, *assigns, record_call]

    def format_assign(self, node: ast.Assign) -> FormattedAstNode | None:
        if not node.targets:
            return None

        first_target = node.targets[0]
        target_node = self._handlers.handle(first_target)
        value_node = self._handlers.handle(node.value)

        if target_node is None or value_node is None:
            return None

        return FormattedAstNode(
            targets=target_node.expr,
            expr=value_node.expr,
            substitution=value_node.substitution,
        )

    def inject_temp_var(
        self, node: ast.AST, as_node: FormattedAstNode
    ) -> tuple[FormattedAstNode, list[ast.Assign]]:
        """
        将复杂表达式注入临时变量，并返回变量名
        """

        # 提取其中的表达式
        expr = as_node.expr
        substitution = as_node.substitution

        exprs1 = self._extract_sub_expressions(expr)
        exprs2 = self._extract_sub_expressions(substitution)
        all_exprs = set(exprs1 + exprs2)

        # 将表达式注入到临时变量
        assigns = []
        for i, sub_expr in enumerate(all_exprs):
            # 只处理复杂表达式：包含运算符的表达式
            if all(
                op not in sub_expr
                for op in ["+", "-", "*", "/", "**", "//", "%", "(", ")"]
            ):
                continue

            temp_var_name = f"_uzon_temp_var_{i}"
            # 注入临时变量赋值语句
            temp_assign = ast.Assign(
                targets=[ast.Name(id=temp_var_name, ctx=ast.Store())],
                value=ast.parse(sub_expr, mode="eval").body,
            )
            ast.copy_location(temp_assign, node)
            assigns.append(temp_assign)

            # 替换表达式为临时变量名
            expr = expr.replace(f"{{{sub_expr}}}", f"{{{temp_var_name}}}")
            substitution = substitution.replace(
                f"{{{sub_expr}}}", f"{{{temp_var_name}}}"
            )

        new_node = as_node.clone()
        new_node.expr = expr
        new_node.substitution = substitution

        return (new_node, assigns)

    def _extract_sub_expressions(self, expr: str) -> list[str]:
        """
        提取表达式中的子表达式
        :expr: 示例 '{10 * unit.m / unit.second} + {2 * unit.m / unit.second}'
        """

        exprs = []
        start = expr.find("{")
        while start != -1:
            end = expr.find("}", start)
            if end == -1:
                break

            sub_expr = expr[start + 1 : end]
            exprs.append(sub_expr)
            start = expr.find("{", end)
        return exprs
