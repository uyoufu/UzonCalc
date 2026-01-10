"""AST 安全验证器，确保插桩后的代码安全"""

import ast
from typing import Set

from core.handcalc.exceptions import ValidationError

# description
# 本模块用于验证插桩后的 AST 树，确保其中只包含允许的节点类型。
# 这样可以防止插桩过程中引入不安全或不受支持的代码结构。

# 允许的 AST 节点类型白名单
ALLOWED_AST_NODES: Set[type] = {
    # 模块和函数定义
    ast.Module,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Return,
    ast.Delete,
    ast.Assign,
    ast.AugAssign,
    ast.AnnAssign,
    # 导入语句
    ast.Import,
    ast.ImportFrom,
    # 控制流
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.If,
    ast.With,
    ast.AsyncWith,
    ast.Match,
    ast.match_case,
    ast.Raise,
    ast.Try,
    ast.Assert,
    ast.Pass,
    ast.Break,
    ast.Continue,
    # 表达式
    ast.Expr,
    ast.BoolOp,
    ast.NamedExpr,
    ast.BinOp,
    ast.UnaryOp,
    ast.Lambda,
    ast.IfExp,
    ast.Dict,
    ast.Set,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
    ast.Await,
    ast.Yield,
    ast.YieldFrom,
    ast.Compare,
    ast.Call,
    ast.FormattedValue,
    ast.JoinedStr,
    ast.Constant,
    ast.Attribute,
    ast.Subscript,
    ast.Starred,
    ast.Name,
    ast.List,
    ast.Tuple,
    ast.Slice,
    # 操作符
    ast.Load,
    ast.Store,
    ast.Del,
    ast.And,
    ast.Or,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.MatMult,
    ast.Div,
    ast.Mod,
    ast.Pow,
    ast.LShift,
    ast.RShift,
    ast.BitOr,
    ast.BitXor,
    ast.BitAnd,
    ast.FloorDiv,
    ast.Invert,
    ast.Not,
    ast.UAdd,
    ast.USub,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Is,
    ast.IsNot,
    ast.In,
    ast.NotIn,
    # 其他
    ast.comprehension,
    ast.ExceptHandler,
    ast.arguments,
    ast.arg,
    ast.keyword,
    ast.alias,
    ast.withitem,
}


class AstValidator(ast.NodeVisitor):
    """AST 验证器，检查节点是否在白名单中"""

    def __init__(self) -> None:
        self.violations: list[str] = []

    def visit(self, node: ast.AST) -> None:
        node_type = type(node)
        if node_type not in ALLOWED_AST_NODES:
            self.violations.append(
                f"Disallowed AST node: {node_type.__name__} at line {getattr(node, 'lineno', '?')}"
            )
        self.generic_visit(node)

    def validate(self, tree: ast.Module) -> None:
        """验证 AST 树，如果有违规则抛出异常"""
        self.violations.clear()
        self.visit(tree)
        if self.violations:
            raise ValidationError(
                f"AST validation failed:\n" + "\n".join(self.violations)
            )


def validate_ast(tree: ast.Module) -> None:
    """验证 AST 树的安全性"""
    validator = AstValidator()
    validator.validate(tree)
