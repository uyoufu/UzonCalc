from __future__ import annotations

import ast
from functools import singledispatch
from typing import Any, List, Optional
from core.units import unit
from pint.util import UnitsContainer
from . import ir
from .unit_collector import UnitExpressionCollector, unit_powers_to_expr


def _unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


# 操作符映射表
_UNARY_OPS: dict[type, str] = {
    ast.UAdd: "+",
    ast.USub: "-",
    ast.Not: "¬",
    ast.Invert: "~",
}

_CMP_OPS: dict[type, str] = {
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
    # 布尔值和 None 的统一处理
    return ir.mtext(str(v) if v is not None else "None")


@expr_to_ir.register(ast.UnaryOp)
def _expr_unary(node: ast.UnaryOp) -> ir.MathNode:
    if (symbol := _UNARY_OPS.get(type(node.op))) is not None:
        return ir.mrow([ir.mo(symbol), expr_to_ir(node.operand)])
    return ir.mtext(_unparse(node))


# 二元操作符映射: (symbol, is_infix) 或 None 表示特殊处理
_BINOP_INFIX: dict[type, str] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "·",
    ast.FloorDiv: "//",
    ast.Mod: "%",
}


@expr_to_ir.register(ast.BinOp)
def _expr_binop(node: ast.BinOp) -> ir.MathNode:
    # 特殊处理单位表达式
    if (folded := _try_fold_unit_expr_as_single_mu(node)) is not None:
        if (numeric := _extract_numeric_part(node)) is not None:
            return ir.mrow([numeric, ir.mo(""), folded])
        return folded

    left, right = expr_to_ir(node.left), expr_to_ir(node.right)
    op_type = type(node.op)

    # 中缀操作符
    if (symbol := _BINOP_INFIX.get(op_type)) is not None:
        return ir.mrow([left, ir.mo(symbol), right])
    # 特殊操作符
    if op_type is ast.Div:
        return ir.mfrac(left, right)
    if op_type is ast.Pow:
        return ir.msup(left, right)
    return ir.mtext(_unparse(node))


@expr_to_ir.register(ast.BoolOp)
def _expr_boolop(node: ast.BoolOp) -> ir.MathNode:
    op = "∧" if isinstance(node.op, ast.And) else "∨"
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
        items.append(ir.mo(_CMP_OPS.get(type(op), op.__class__.__name__)))
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


# _cmp_op_to_str 已由 _CMP_OPS 字典替代


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

    # 构建单位节点（只包含单位部分，不包含系数）
    units = unit.parse_units(unit_powers_to_expr(collector.unit_powers))
    return ir.mu(str(units))


def _extract_numeric_part(node: ast.AST) -> Optional[ir.MathNode]:
    """从包含单位的表达式中提取纯数值计算部分"""
    if not isinstance(node, ast.BinOp):
        return None

    def _is_unit_node(n: ast.AST) -> bool:
        """检查是否为单位相关节点"""
        if (
            isinstance(n, ast.Attribute)
            and isinstance(n.value, ast.Name)
            and n.value.id == "unit"
        ):
            return True
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow):
            return _is_unit_node(n.left)
        return False

    def _extract(n: ast.AST) -> Optional[ir.MathNode]:
        """递归提取数值部分"""
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return ir.mn(n.value)
        if isinstance(n, ast.UnaryOp):
            # 处理带符号的数值（如 -15）
            # 如果操作数是常量，直接应用符号到数值
            if isinstance(n.operand, ast.Constant) and isinstance(
                n.operand.value, (int, float)
            ):
                if isinstance(n.op, ast.USub):
                    return ir.mn(-n.operand.value)
                elif isinstance(n.op, ast.UAdd):
                    return ir.mn(n.operand.value)
            # 对于更复杂的表达式，递归提取
            operand = _extract(n.operand)
            if operand is not None:
                symbol = _UNARY_OPS.get(type(n.op), "")
                return ir.mrow([ir.mo(symbol), operand])
            return None
        if _is_unit_node(n):
            return None
        if isinstance(n, ast.BinOp):
            left, right = _extract(n.left), _extract(n.right)
            if left and right:
                return (
                    ir.mrow([left, ir.mo("·"), right])
                    if isinstance(n.op, ast.Mult)
                    else ir.mfrac(left, right)
                )
            return left or right
        return None

    return _extract(node)
