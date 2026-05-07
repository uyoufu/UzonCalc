from __future__ import annotations

import ast

from .. import ir

# 操作符映射表
UNARY_OPS: dict[type, str] = {
    ast.UAdd: "+",
    ast.USub: "-",
    ast.Not: "¬",
    ast.Invert: "~",
}

CMP_OPS: dict[type, str] = {
    ast.Eq: "≡",
    ast.NotEq: "≠",
    ast.Lt: "<",
    ast.LtE: "≤",
    ast.Gt: ">",
    ast.GtE: "≥",
    ast.In: "in",
    ast.NotIn: "not in",
    ast.Is: "is",
    ast.IsNot: "is not",
}

# 二元操作符映射: (symbol, is_infix) 或 None 表示特殊处理
BINOP_INFIX: dict[type, str] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "·",
    ast.FloorDiv: "//",
    ast.Mod: "%",
}

# 操作符优先级（数值越大优先级越高）
BINOP_PRECEDENCE: dict[type, int] = {
    ast.Add: 1,
    ast.Sub: 1,
    ast.Mult: 2,
    ast.Div: 2,
    ast.FloorDiv: 2,
    ast.Mod: 2,
    ast.Pow: 3,
}


def needs_parens(child: ast.AST, parent_op: type) -> bool:
    """判断子表达式是否需要括号

    当子表达式的操作符优先级低于父操作符时，需要括号
    """
    if not isinstance(child, ast.BinOp):
        return False
    child_prec = BINOP_PRECEDENCE.get(type(child.op), 0)
    parent_prec = BINOP_PRECEDENCE.get(parent_op, 0)
    return child_prec < parent_prec


def maybe_parenthesize_left(
    child_ast: ast.AST, parent_op: type, child_ir: ir.MathNode
) -> ir.MathNode:
    """检查是否需要给左子节点添加括号。"""
    if needs_parens(child_ast, parent_op):
        return ir.mrow([ir.mo("("), child_ir, ir.mo(")")])
    return child_ir


def maybe_parenthesize_right(
    child_ast: ast.AST, parent_op: type, child_ir: ir.MathNode
) -> ir.MathNode:
    """检查是否需要给右子节点添加括号。

    对于减法和除法，右侧即使同优先级也需要括号（因为不满足结合律）。
    由于除法采用分数形式展示，这里只需考虑减法情况。
    """
    if needs_parens(child_ast, parent_op):
        return ir.mrow([ir.mo("("), child_ir, ir.mo(")")])

    if isinstance(child_ast, ast.BinOp) and parent_op is ast.Sub:
        # 对于 a - (b + c) 或 a / (b * c) 这类情况，右侧同优先级也需要括号
        child_prec = BINOP_PRECEDENCE.get(type(child_ast.op), 0)
        parent_prec = BINOP_PRECEDENCE.get(parent_op, 0)
        if child_prec == parent_prec:
            return ir.mrow([ir.mo("("), child_ir, ir.mo(")")])

    return child_ir
