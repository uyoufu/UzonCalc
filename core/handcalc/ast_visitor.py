import ast
from typing import Optional

from core.handcalc.field_names import FieldNames
from core.handcalc.recording_state import RecordingState
from core.handcalc.ast_to_step import AstToStepConverter
from core.handcalc.recording_injector import RecordingInjector
from core.handcalc import ir

# description:
# 本模块定义了一个 AST 访问器类，用于遍历和修改 AST 树，
# 以插入记录计算步骤的调用，从而实现对代码执行过程的跟踪和记录。


class AstNodeVisitor(ast.NodeTransformer):
    def __init__(self) -> None:
        super().__init__()
        self._state = RecordingState()
        self._converter = AstToStepConverter()
        self._injector = RecordingInjector()

    def _visit_body_scope(self, node: ast.AST, body_attr: str = "body") -> ast.AST:
        """通用的作用域访问方法，处理带有 body 的节点"""
        body = getattr(node, body_attr)
        self._mark_docstring_skip(body)
        prev = self._state.enabled
        self._state.enable()
        setattr(node, body_attr, self._transform_stmt_block(body))
        if not prev:
            self._state.disable()
        return node

    def visit_Module(self, node: ast.Module) -> ast.AST:
        return self._visit_body_scope(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        return self._visit_body_scope(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        return self._visit_body_scope(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        return self._visit_body_scope(node)

    def _visit_loop(self, node: ast.For | ast.AsyncFor | ast.While) -> ast.AST:
        """通用循环访问方法"""
        if hasattr(node, "target"):
            node.target = self.visit(node.target)  # type: ignore[assignment]
        if hasattr(node, "iter"):
            node.iter = self.visit(node.iter)  # type: ignore[assignment]
        if hasattr(node, "test"):
            node.test = self.visit(node.test)  # type: ignore[assignment]
        node.body = self._transform_stmt_block(node.body)
        node.orelse = self._transform_stmt_block(node.orelse)
        return node

    def visit_If(self, node: ast.If) -> ast.AST:
        node.test = self.visit(node.test)  # type: ignore[assignment]
        node.body = self._transform_stmt_block(node.body)
        node.orelse = self._transform_stmt_block(node.orelse)
        return node

    def visit_For(self, node: ast.For) -> ast.AST:
        return self._visit_loop(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> ast.AST:
        return self._visit_loop(node)

    def visit_While(self, node: ast.While) -> ast.AST:
        return self._visit_loop(node)

    def _visit_with(self, node: ast.With | ast.AsyncWith) -> ast.AST:
        """通用 with 语句访问方法"""
        node.items = [self.visit(i) for i in node.items]  # type: ignore[assignment]
        node.body = self._transform_stmt_block(node.body)
        return node

    def visit_With(self, node: ast.With) -> ast.AST:
        return self._visit_with(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> ast.AST:
        return self._visit_with(node)

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
        """访问赋值语句节点"""
        self.generic_visit(node)

        # Skip when marked.
        if getattr(node, FieldNames.skip_record, False):
            return node

        # 使用转换器转换为 Step
        step = self._converter.convert_assign(node)

        # 获取值节点
        value_node: Optional[ast.expr] = None
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            value_node = ast.Name(id=node.targets[0].id, ctx=ast.Load())

        # 使用注入器生成记录调用
        record_call = self._injector.make_record_call(
            node, step=step, value_node=value_node
        )
        return [node, record_call]

    def visit_Expr(self, node: ast.Expr) -> ast.AST | list[ast.stmt]:
        """访问表达式语句节点"""
        self.generic_visit(node)

        # Skip when marked.
        if getattr(node, FieldNames.skip_record, False):
            return node

        # Control directives: used to toggle instrumentation; never recorded.
        if self._is_toggle_directive(
            node, FieldNames.directive_hide
        ) or self._is_toggle_directive(node, FieldNames.directive_show):
            setattr(node, FieldNames.skip_record, True)
            return node

        if isinstance(node.value, ast.Call):
            # Function call expression -> no recording.
            return node

        # Pure string literal statement (non-docstring) -> text output.
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            step = self._converter.convert_string_expr(node.value.value)
            record_call = self._injector.make_record_call(
                node, step=step, include_locals=False
            )
            return [node, record_call]

        # f-string expression statement -> capture values + record as formulas.
        if isinstance(node.value, ast.JoinedStr):
            stmts: list[ast.stmt] = []
            value_vars: list[str] = []
            formatted_value_idx = 0

            # Generate temp variables to capture each formatted value.
            for idx, v in enumerate(node.value.values):
                if isinstance(v, ast.FormattedValue):
                    temp_var = f"__fstring_val_{formatted_value_idx}__"
                    formatted_value_idx += 1
                    value_vars.append(temp_var)
                    
                    # 如果有格式化规范，应用格式化；否则直接使用表达式
                    if v.format_spec:
                        # 提取格式化规范字符串
                        format_spec = ""
                        if isinstance(v.format_spec, ast.JoinedStr):
                            for spec_val in v.format_spec.values:
                                if isinstance(spec_val, ast.Constant) and isinstance(spec_val.value, str):
                                    format_spec += spec_val.value
                        
                        # 创建格式化表达式：format(expr, format_spec)
                        format_call = ast.Call(
                            func=ast.Name(id="format", ctx=ast.Load()),
                            args=[v.value, ast.Constant(value=format_spec)],
                            keywords=[],
                        )
                        ast.copy_location(format_call, node)
                        value_expr = format_call
                    else:
                        value_expr = v.value
                    
                    # Create: __fstring_val_N__ = <expr> or format(<expr>, format_spec)
                    assign = ast.Assign(
                        targets=[ast.Name(id=temp_var, ctx=ast.Store())],
                        value=value_expr,
                    )
                    ast.copy_location(assign, node)
                    stmts.append(assign)

            step = self._converter.convert_fstring(node.value, value_vars)
            record_call = self._injector.make_record_call(
                node,
                step=step,
                include_locals=True,
            )
            stmts.extend([node, record_call])
            return stmts

        # Special case: a bare variable name -> show as `name = value`.
        if isinstance(node.value, ast.Name) and isinstance(node.value.ctx, ast.Load):
            step = self._converter.convert_name_expr(node.value.id)
            record_call = self._injector.make_record_call(
                node,
                step=step,
                value_node=ast.Name(id=node.value.id, ctx=ast.Load()),
                include_locals=True,
            )
            return [node, record_call]

        # General expression statement -> math output.
        step = self._converter.convert_expr(node.value)
        record_call = self._injector.make_record_call(
            node, step=step, include_locals=True
        )
        return [node, record_call]

    # region 内部方法
    def _mark_docstring_skip(self, body: list[ast.stmt]) -> None:
        """若第一个语句是字符串常量（文档字符串），则标记其跳过记录"""
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
            if self._is_toggle_directive(stmt, FieldNames.directive_hide):
                self._state.disable()
                setattr(stmt, FieldNames.skip_record, True)
                out.append(stmt)
                continue

            if self._is_toggle_directive(stmt, FieldNames.directive_show):
                self._state.enable()
                setattr(stmt, FieldNames.skip_record, True)
                out.append(stmt)
                continue

            if not self._state.enabled:
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
