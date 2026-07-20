from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum

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


class BinOpChildSide(Enum):
    """二元表达式子节点相对父算符的位置。"""

    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True, slots=True)
class OperatorContext:
    """表达式渲染时由父算符传递给子表达式的优先级上下文。"""

    parent_op: type
    child_side: BinOpChildSide


def needs_parens(child: ast.AST, parent_op: type) -> bool:
    """判断子表达式是否需要括号

    当子表达式的操作符优先级低于父操作符时，需要括号
    """
    if not isinstance(child, ast.BinOp):
        return False
    child_prec = BINOP_PRECEDENCE.get(type(child.op), 0)
    parent_prec = BINOP_PRECEDENCE.get(parent_op, 0)
    return child_prec < parent_prec


def apply_operator_context_parentheses(
    child_ast: ast.AST, child_ir: ir.MathNode, context: OperatorContext | None
) -> ir.MathNode:
    """根据父算符上下文为子表达式补充必要括号。"""
    if context is None or not isinstance(child_ast, ast.BinOp):
        return child_ir

    if needs_parens(child_ast, context.parent_op):
        return _parenthesize(child_ir)

    if context.child_side is BinOpChildSide.RIGHT and context.parent_op is ast.Sub:
        child_prec = BINOP_PRECEDENCE.get(type(child_ast.op), 0)
        parent_prec = BINOP_PRECEDENCE.get(context.parent_op, 0)
        if child_prec == parent_prec:
            return _parenthesize(child_ir)

    return child_ir


def maybe_parenthesize_left(
    child_ast: ast.AST, parent_op: type, child_ir: ir.MathNode
) -> ir.MathNode:
    """检查是否需要给左子节点添加括号。"""
    return apply_operator_context_parentheses(
        child_ast, child_ir, OperatorContext(parent_op, BinOpChildSide.LEFT)
    )


def maybe_parenthesize_right(
    child_ast: ast.AST, parent_op: type, child_ir: ir.MathNode
) -> ir.MathNode:
    """检查是否需要给右子节点添加括号。

    对于减法和除法，右侧即使同优先级也需要括号（因为不满足结合律）。
    由于除法采用分数形式展示，这里只需考虑减法情况。
    """
    return apply_operator_context_parentheses(
        child_ast, child_ir, OperatorContext(parent_op, BinOpChildSide.RIGHT)
    )


def _parenthesize(node: ir.MathNode) -> ir.MathNode:
    """构造显式括号节点。"""
    return ir.mrow([ir.mo("("), node, ir.mo(")")])
