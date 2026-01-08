import ast

from core.handcalc.field_names import FieldNames
from core.handcalc.v2.ast_to_ir import expr_to_ir, target_to_ir
from core.handcalc.v2 import ir


class AstNodeVisitor(ast.NodeTransformer):
    def __init__(self) -> None:
        super().__init__()

    def _make_record_call(
        self,
        original_node: ast.AST,
        *,
        step: dict,
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

    def _step_to_ast(self, step: dict) -> ast.expr:
        keys: list[ast.expr | None] = []
        values: list[ast.expr] = []
        for k, v in step.items():
            keys.append(ast.Constant(value=k))
            values.append(self._value_to_ast(v))
        return ast.Dict(keys=keys, values=values)

    def _value_to_ast(self, value: object) -> ast.expr:
        if value is None or isinstance(value, (bool, int, float, str)):
            return ast.Constant(value=value)

        if isinstance(value, ir.MathNode) or isinstance(value, str):
            return self._math_to_ast(value)  # type: ignore[arg-type]

        if isinstance(value, list):
            return ast.List(elts=[self._value_to_ast(v) for v in value], ctx=ast.Load())

        if isinstance(value, dict):
            return self._step_to_ast(value)

        return ast.Constant(value=str(value))

    def _ir_func(self, name: str) -> ast.expr:
        return ast.Attribute(
            value=ast.Name(id=FieldNames.uzon_ir, ctx=ast.Load()),
            attr=name,
            ctx=ast.Load(),
        )

    def _math_to_ast(self, node: ir.Math) -> ast.expr:
        if node is None:
            return ast.Constant(value=None)

        if isinstance(node, str):
            # Renderer treats bare strings as <mtext>.
            return ast.Constant(value=node)

        if isinstance(node, ir.Mi):
            return ast.Call(
                func=self._ir_func("mi"),
                args=[ast.Constant(value=node.name)],
                keywords=[],
            )

        if isinstance(node, ir.Mn):
            return ast.Call(
                func=self._ir_func("mn"),
                args=[ast.Constant(value=node.value)],
                keywords=[],
            )

        if isinstance(node, ir.Mo):
            return ast.Call(
                func=self._ir_func("mo"),
                args=[ast.Constant(value=node.symbol)],
                keywords=[],
            )

        if isinstance(node, ir.MText):
            return ast.Call(
                func=self._ir_func("mtext"),
                args=[ast.Constant(value=node.text)],
                keywords=[],
            )

        if isinstance(node, ir.MRow):
            children_ast = ast.List(
                elts=[self._math_to_ast(ch) for ch in node.children],
                ctx=ast.Load(),
            )
            return ast.Call(
                func=self._ir_func("mrow"), args=[children_ast], keywords=[]
            )

        if isinstance(node, ir.MFrac):
            return ast.Call(
                func=self._ir_func("mfrac"),
                args=[
                    self._math_to_ast(node.numerator),
                    self._math_to_ast(node.denominator),
                ],
                keywords=[],
            )

        if isinstance(node, ir.MSup):
            return ast.Call(
                func=self._ir_func("msup"),
                args=[self._math_to_ast(node.base), self._math_to_ast(node.exponent)],
                keywords=[],
            )

        if isinstance(node, ir.MSub):
            return ast.Call(
                func=self._ir_func("msub"),
                args=[self._math_to_ast(node.base), self._math_to_ast(node.subscript)],
                keywords=[],
            )

        if isinstance(node, ir.MSqrt):
            return ast.Call(
                func=self._ir_func("msqrt"),
                args=[self._math_to_ast(node.body)],
                keywords=[],
            )

        if isinstance(node, ir.MFenced):
            return ast.Call(
                func=self._ir_func("mfenced"),
                args=[self._math_to_ast(node.body)],
                keywords=[
                    ast.keyword(arg="open", value=ast.Constant(value=node.open)),
                    ast.keyword(arg="close", value=ast.Constant(value=node.close)),
                ],
            )

        return ast.Call(
            func=self._ir_func("mtext"),
            args=[ast.Constant(value=str(node))],
            keywords=[],
        )

    def _mark_docstring_skip(self, body: list[ast.stmt] | None) -> None:
        if not body:
            return
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            setattr(first, FieldNames.skip_record, True)

    def visit_Module(self, node: ast.Module) -> ast.AST:
        self._mark_docstring_skip(getattr(node, "body", None))
        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self._mark_docstring_skip(getattr(node, "body", None))
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        self._mark_docstring_skip(getattr(node, "body", None))
        return self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        self._mark_docstring_skip(getattr(node, "body", None))
        return self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> ast.AST | list[ast.stmt]:
        """
        访问赋值语句节点
        如：x = 5 + 3
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
        step = {"kind": "equation", "lhs": lhs_ir, "rhs": rhs_ir}

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

        # Pure string literal statement (non-docstring) -> text output.
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            step = {"kind": "text", "text": node.value.value}
            record_call = self._make_record_call(node, step=step, include_locals=False)
            return [node, record_call]

        # f-string expression statement -> record evaluated runtime string.
        if isinstance(node.value, ast.JoinedStr):
            step = {"kind": "text", "text": ""}
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
            step = {"kind": "equation", "lhs": ir.mi(node.value.id), "rhs": None}
            record_call = self._make_record_call(
                node,
                step=step,
                value_node=ast.Name(id=node.value.id, ctx=ast.Load()),
                include_locals=True,
            )
            return [node, record_call]

        step = {"kind": "expr", "expr": expr_ir}
        record_call = self._make_record_call(node, step=step, include_locals=True)
        return [node, record_call]
