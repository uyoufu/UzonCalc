import ast

from core.handcalc.field_names import FieldNames
from core.handcalc import steps
from core.handcalc.ast_to_ir import expr_to_ir, target_to_ir
from core.handcalc import ir


class AstNodeVisitor(ast.NodeTransformer):
    def __init__(self) -> None:
        super().__init__()
        # When disabled, we do not instrument/visit subsequent statements
        # (same-level and child statements) until a show() directive appears.
        self._recording_enabled: bool = True

    def visit_Module(self, node: ast.Module) -> ast.AST:
        self._mark_docstring_skip(node.body)
        prev = self._recording_enabled
        self._recording_enabled = True
        node.body = self._transform_stmt_block(node.body)
        self._recording_enabled = prev
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self._mark_docstring_skip(node.body)

        # Each function gets its own instrumentation toggle scope.
        prev = self._recording_enabled
        self._recording_enabled = True
        node.body = self._transform_stmt_block(node.body)
        self._recording_enabled = prev
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        self._mark_docstring_skip(node.body)

        prev = self._recording_enabled
        self._recording_enabled = True
        node.body = self._transform_stmt_block(node.body)
        self._recording_enabled = prev
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        self._mark_docstring_skip(node.body)

        prev = self._recording_enabled
        self._recording_enabled = True
        node.body = self._transform_stmt_block(node.body)
        self._recording_enabled = prev
        return node

    def visit_If(self, node: ast.If) -> ast.AST:
        # Only rewrite statement lists; expressions can use generic_visit.
        node.test = self.visit(node.test)  # type: ignore[assignment]
        node.body = self._transform_stmt_block(node.body)
        node.orelse = self._transform_stmt_block(node.orelse)
        return node

    def visit_For(self, node: ast.For) -> ast.AST:
        node.target = self.visit(node.target)  # type: ignore[assignment]
        node.iter = self.visit(node.iter)  # type: ignore[assignment]
        node.body = self._transform_stmt_block(node.body)
        node.orelse = self._transform_stmt_block(node.orelse)
        return node

    def visit_AsyncFor(self, node: ast.AsyncFor) -> ast.AST:
        node.target = self.visit(node.target)  # type: ignore[assignment]
        node.iter = self.visit(node.iter)  # type: ignore[assignment]
        node.body = self._transform_stmt_block(node.body)
        node.orelse = self._transform_stmt_block(node.orelse)
        return node

    def visit_While(self, node: ast.While) -> ast.AST:
        node.test = self.visit(node.test)  # type: ignore[assignment]
        node.body = self._transform_stmt_block(node.body)
        node.orelse = self._transform_stmt_block(node.orelse)
        return node

    def visit_With(self, node: ast.With) -> ast.AST:
        node.items = [self.visit(i) for i in node.items]  # type: ignore[assignment]
        node.body = self._transform_stmt_block(node.body)
        return node

    def visit_AsyncWith(self, node: ast.AsyncWith) -> ast.AST:
        node.items = [self.visit(i) for i in node.items]  # type: ignore[assignment]
        node.body = self._transform_stmt_block(node.body)
        return node

    def visit_Try(self, node: ast.Try) -> ast.AST:
        node.body = self._transform_stmt_block(node.body)
        node.orelse = self._transform_stmt_block(node.orelse)
        node.finalbody = self._transform_stmt_block(node.finalbody)
        node.handlers = [self.visit(h) for h in node.handlers]  # type: ignore[assignment]
        return node

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> ast.AST:
        if node.type is not None:
            node.type = self.visit(node.type)  # type: ignore[assignment]
        node.body = self._transform_stmt_block(node.body)
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.AST | list[ast.stmt]:
        """
        访问赋值语句节点
        """
        self.generic_visit(node)

        # Skip when marked.
        if getattr(node, FieldNames.skip_record, False):
            return node

        # Build lhs/rhs IR.
        # lhs: left-hand side
        # rhs: right-hand side
        if len(node.targets) == 1:
            lhs_ir = target_to_ir(node.targets[0])
        else:
            # Multi-target assignment: keep readable.
            try:
                lhs_ir = ir.mtext(", ".join(ast.unparse(t) for t in node.targets))
            except Exception:
                lhs_ir = ir.mtext("<targets>")

        rhs_ir = expr_to_ir(node.value)
        step = steps.EquationStep(lhs=lhs_ir, rhs=rhs_ir)

        # 获取值节点
        value_node: ast.expr | None = None
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            value_node = ast.Name(id=node.targets[0].id, ctx=ast.Load())

        record_call = self._make_record_call(node, step=step, value_node=value_node)
        return [node, record_call]

    def visit_Expr(self, node: ast.Expr) -> ast.AST | list[ast.stmt]:
        """
        访问表达式语句节点
        有：
        1. 函数调用表达式，如：print(x)
        2. 字面量表达式，如：42
        3. 变量名表达式，如：x
        4. 复杂表达式，如：(a + b) * c
        """
        self.generic_visit(node)

        # Skip when marked.
        if getattr(node, FieldNames.skip_record, False):
            return node

        # Control directives: used to toggle instrumentation; never recorded.
        if self._is_toggle_directive(node, "hide") or self._is_toggle_directive(
            node, "show"
        ):
            setattr(node, FieldNames.skip_record, True)
            return node

        if isinstance(node.value, ast.Call):
            # Function call expression -> no recording.
            return node

        # Pure string literal statement (non-docstring) -> text output.
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            step = steps.TextStep(text=node.value.value)
            record_call = self._make_record_call(node, step=step, include_locals=False)
            return [node, record_call]

        # f-string expression statement -> record evaluated runtime string.
        if isinstance(node.value, ast.JoinedStr):
            step = steps.TextStep(text="")
            record_call = self._make_record_call(
                node,
                step=step,
                value_node=node.value,
                include_locals=False,
            )
            return [node, record_call]

        # General expression statement -> math output.
        expr_ir = expr_to_ir(node.value)

        # Special case: a bare variable name -> show as `name = value`.
        if isinstance(node.value, ast.Name) and isinstance(node.value.ctx, ast.Load):
            step = steps.EquationStep(lhs=ir.mi(node.value.id), rhs=None)
            record_call = self._make_record_call(
                node,
                step=step,
                value_node=ast.Name(id=node.value.id, ctx=ast.Load()),
                include_locals=True,
            )
            return [node, record_call]

        step = steps.ExprStep(expr=expr_ir)
        record_call = self._make_record_call(node, step=step, include_locals=True)
        return [node, record_call]

    # region 内部方法
    def _make_record_call(
        self,
        original_node: ast.AST,
        *,
        step: steps.Step,
        value_node: ast.expr | None = None,
        include_locals: bool = True,
    ) -> ast.Expr:
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
        return self._step_obj_to_ast(step)

    def _step_obj_to_ast(self, step: steps.Step) -> ast.expr:
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

        # Fallback: stringify step.
        ctor = ast.Attribute(value=steps_mod, attr="TextStep", ctx=ast.Load())
        return ast.Call(
            func=ctor,
            args=[],
            keywords=[ast.keyword(arg="text", value=ast.Constant(value=str(step)))],
        )

    def _value_to_ast(self, value: object) -> ast.expr:
        if value is None or isinstance(value, (bool, int, float, str)):
            return ast.Constant(value=value)

        if isinstance(value, ir.MathNode):
            return self._math_to_ast(value)

        if isinstance(value, list):
            return ast.List(elts=[self._value_to_ast(v) for v in value], ctx=ast.Load())

        if isinstance(value, dict):
            keys: list[ast.expr | None] = []
            values: list[ast.expr] = []
            for k, v in value.items():
                keys.append(ast.Constant(value=k))
                values.append(self._value_to_ast(v))
            return ast.Dict(keys=keys, values=values)

        return ast.Constant(value=str(value))

    def _math_to_ast(self, node: ir.MathNode | str) -> ast.expr:
        if isinstance(node, str):
            # Shouldn't happen for v2 IR; keep a safe fallback.
            return ast.Constant(value=node)
        return node.to_python_ast(ir_var_name=FieldNames.uzon_ir)

    def _mark_docstring_skip(self, body: list[ast.stmt]) -> None:
        """
        若第一个语句是字符串常量（文档字符串），则标记其跳过记录
        暂时保留
        """
        if not body:
            return
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            setattr(first, FieldNames.skip_record, True)

    def _is_toggle_directive(self, node: ast.AST, name: str) -> bool:
        return (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == name
            and len(node.value.args) == 0
            and len(node.value.keywords) == 0
        )

    def _transform_stmt_block(self, body: list[ast.stmt]) -> list[ast.stmt]:
        """Transform a list of statements in lexical order.

        When hidden (after hide()), statements are left untouched and we do not
        visit/instrument their child nodes until a show() directive appears.
        """

        if not body:
            return body

        out: list[ast.stmt] = []
        for stmt in body:
            if self._is_toggle_directive(stmt, "hide"):
                self._recording_enabled = False
                setattr(stmt, FieldNames.skip_record, True)
                out.append(stmt)
                continue

            if self._is_toggle_directive(stmt, "show"):
                self._recording_enabled = True
                setattr(stmt, FieldNames.skip_record, True)
                out.append(stmt)
                continue

            if not self._recording_enabled:
                # Do not visit / instrument this statement or any children.
                out.append(stmt)
                continue

            visited = self.visit(stmt)
            if visited is None:
                continue
            if isinstance(visited, list):
                out.extend(visited)
            else:
                out.append(visited)  # type: ignore[arg-type]

        return out

    # endregion
