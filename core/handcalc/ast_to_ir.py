from __future__ import annotations

import ast
from functools import singledispatch
from typing import Any, List, Optional
from core.units import unit
from pint.util import UnitsContainer
from . import ir
from .unit_collector import UnitExpressionCollector


def _unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


def target_to_ir(node: ast.AST) -> ir.MathNode:
    # Targets are often Name/Attribute/Subscript/Tuple/List/Starred.
    if isinstance(node, ast.Name):
        return ir.mi(node.id)

    # Fallback for complex targets: keep readable.
    return ir.mtext(_unparse(node))


@singledispatch
def expr_to_ir(node: ast.AST) -> ir.MathNode:
    """
    Convert a Python AST expression node into a Math IR node.

    使用 singledispatch 实现，支持扩展新的 AST 节点类型。
    """
    # 默认回退：对于未知类型，使用 unparse
    return ir.mtext(_unparse(node))


@expr_to_ir.register(ast.Name)
def _expr_name(node: ast.Name) -> ir.MathNode:
    return ir.mi(node.id)


@expr_to_ir.register(ast.Constant)
def _expr_constant(node: ast.Constant) -> ir.MathNode:
    v = node.value
    if isinstance(v, (int, float)):
        return ir.mn(v)
    if isinstance(v, str):
        return ir.mtext(v)
    if v is None:
        return ir.mtext("None")
    if v is True:
        return ir.mtext("True")
    if v is False:
        return ir.mtext("False")
    return ir.mtext(str(v))


@expr_to_ir.register(ast.UnaryOp)
def _expr_unary(node: ast.UnaryOp) -> ir.MathNode:
    operand = expr_to_ir(node.operand)
    if isinstance(node.op, ast.UAdd):
        return ir.mrow([ir.mo("+"), operand])
    if isinstance(node.op, ast.USub):
        return ir.mrow([ir.mo("-"), operand])
    if isinstance(node.op, ast.Not):
        return ir.mrow([ir.mo("not"), operand])
    if isinstance(node.op, ast.Invert):
        return ir.mrow([ir.mo("~"), operand])
    return ir.mtext(_unparse(node))


@expr_to_ir.register(ast.BinOp)
def _expr_binop(node: ast.BinOp) -> ir.MathNode:
    # 特殊处理单位表达式
    folded = _try_fold_unit_expr_as_single_mu(node)
    if folded is not None:
        return folded

    left = expr_to_ir(node.left)
    right = expr_to_ir(node.right)

    if isinstance(node.op, ast.Add):
        return ir.mrow([left, ir.mo("+"), right])
    if isinstance(node.op, ast.Sub):
        return ir.mrow([left, ir.mo("-"), right])
    if isinstance(node.op, ast.Mult):
        return ir.mrow([left, ir.mo("·"), right])
    if isinstance(node.op, ast.Div):
        return ir.mfrac(left, right)
    if isinstance(node.op, ast.FloorDiv):
        return ir.mrow([left, ir.mo("//"), right])
    if isinstance(node.op, ast.Mod):
        return ir.mrow([left, ir.mo("%"), right])
    if isinstance(node.op, ast.Pow):
        return ir.msup(left, right)

    return ir.mtext(_unparse(node))


@expr_to_ir.register(ast.BoolOp)
def _expr_boolop(node: ast.BoolOp) -> ir.MathNode:
    op = "and" if isinstance(node.op, ast.And) else "or"
    items: List[ir.MathNode] = []
    for idx, v in enumerate(node.values):
        if idx:
            items.append(ir.mo(op))
        items.append(expr_to_ir(v))
    return ir.mrow(items)


@expr_to_ir.register(ast.Compare)
def _expr_compare(node: ast.Compare) -> ir.MathNode:
    items: List[ir.MathNode] = [expr_to_ir(node.left)]
    for op, comp in zip(node.ops, node.comparators):
        items.append(ir.mo(_cmp_op_to_str(op)))
        items.append(expr_to_ir(comp))
    return ir.mrow(items)


@expr_to_ir.register(ast.Call)
def _expr_call(node: ast.Call) -> ir.MathNode:
    func_name = _unparse(node.func)
    args = [expr_to_ir(a) for a in node.args]

    # Special cases
    if func_name == "abs" and len(args) == 1:
        return ir.mrow([ir.mo("|"), args[0], ir.mo("|")])
    if func_name in ("sqrt", "math.sqrt") and len(args) == 1:
        return ir.msqrt(args[0])

    # Generic function call: f(a, b)
    arg_nodes: List[ir.MathNode] = []
    for idx, a in enumerate(args):
        if idx:
            arg_nodes.append(ir.mo(","))
        arg_nodes.append(a)

    return ir.mrow([ir.mtext(func_name), ir.mo("("), *arg_nodes, ir.mo(")")])


@expr_to_ir.register(ast.Attribute)
def _expr_attribute(node: ast.Attribute) -> ir.MathNode:
    # like unit.meter
    if isinstance(node.value, ast.Name) and node.value.id == "unit":
        return ir.mu(node.attr)
    else:
        return ir.mi(_unparse(node))


def _cmp_op_to_str(op: ast.cmpop) -> str:
    if isinstance(op, ast.Eq):
        return "="
    if isinstance(op, ast.NotEq):
        return "≠"
    if isinstance(op, ast.Lt):
        return "<"
    if isinstance(op, ast.LtE):
        return "≤"
    if isinstance(op, ast.Gt):
        return ">"
    if isinstance(op, ast.GtE):
        return "≥"
    if isinstance(op, ast.In):
        return "in"
    if isinstance(op, ast.NotIn):
        return "not in"
    if isinstance(op, ast.Is):
        return "is"
    if isinstance(op, ast.IsNot):
        return "is not"
    return op.__class__.__name__


def _try_fold_unit_expr_as_single_mu(node: ast.AST) -> Optional[ir.MathNode]:
    """
    遍历乘除法表达式树，提取出其中的单位及其幂次，构造一个单一的 ir.Mu 节点表示该单位表达式
    若没有符合的单位乘除法表达式，返回 None
    """
    if not isinstance(node, ast.BinOp) or not isinstance(
        node.op, (ast.Mult, ast.Div, ast.Pow)
    ):
        return None

    # 使用辅助类来管理状态
    collector = UnitExpressionCollector()
    if not collector.walk(node, +1):
        return None

    if not collector.unit_powers:
        return None

    # 构建单位节点
    return collector.build_unit_node()
