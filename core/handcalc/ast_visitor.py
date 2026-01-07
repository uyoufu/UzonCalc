import ast

from core.handcalc.recorders.assign_recorder import AssignRecorder
from core.handcalc.recorders.expr_recorder import ExprRecorder
from core.handcalc.field_names import FieldNames
from core.handcalc.token_handlers.handlers_factory import TokenHandlerFactory


class AstNodeVisitor(ast.NodeTransformer):
    def __init__(self) -> None:
        super().__init__()
        self.__handlersFactory = TokenHandlerFactory()

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

        # 调用格式化器
        recorder = AssignRecorder(self.__handlersFactory)
        return recorder.record(node)

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

        # 调用格式化器
        recorder = ExprRecorder(self.__handlersFactory)
        return recorder.record(node)
