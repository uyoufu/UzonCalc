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
    folded_result = _try_fold_unit_expr_as_single_mu(node)
    if folded_result is not None:
        # 提取数值计算部分和单位部分
        numeric_part = _extract_numeric_part(node)
        if numeric_part is not None:
            # 构建完整的表达式：数值计算 * 单位
            return ir.mrow([numeric_part, ir.mo(""), folded_result])
        return folded_result

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

    # 构建单位节点（只包含单位部分，不包含系数）
    units = unit.parse_units(unit_powers_to_expr(collector.unit_powers))
    return ir.mu(str(units))


def _extract_numeric_part(node: ast.AST) -> Optional[ir.MathNode]:
    """
    从包含单位的表达式中提取纯数值计算部分
    
    例如：0.1 * 8 * 24 * unit.kN / unit.m**3 
    返回：0.1 * 8 * 24
    """
    if not isinstance(node, ast.BinOp):
        return None
    
    def _extract_numbers(n: ast.AST) -> Optional[ir.MathNode]:
        """递归提取数值部分"""
        # 如果是数值常量，直接转换
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return ir.mn(n.value)
        
        # 如果是单位相关的节点，返回 None
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "unit":
            return None
        
        # 如果是幂运算且基数是单位，返回 None
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow):
            if isinstance(n.left, ast.Attribute) and isinstance(n.left.value, ast.Name) and n.left.value.id == "unit":
                return None
        
        # 如果是二元运算
        if isinstance(n, ast.BinOp):
            left_nums = _extract_numbers(n.left)
            right_nums = _extract_numbers(n.right)
            
            # 如果左右都是数值部分，构建运算
            if left_nums is not None and right_nums is not None:
                if isinstance(n.op, ast.Mult):
                    return ir.mrow([left_nums, ir.mo("·"), right_nums])
                elif isinstance(n.op, ast.Div):
                    return ir.mfrac(left_nums, right_nums)
            
            # 如果只有左边是数值（右边是单位），返回左边
            if left_nums is not None and right_nums is None:
                return left_nums
            
            # 如果只有右边是数值（左边是单位），返回右边
            if left_nums is None and right_nums is not None:
                return right_nums
        
        return None
    
    return _extract_numbers(node)
