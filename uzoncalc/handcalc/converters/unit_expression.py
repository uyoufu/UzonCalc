from __future__ import annotations

import ast

from ...units import unit
from .. import ir
from ..unit_collector import UnitExpressionCollector, unit_powers_to_expr
from .operator_rendering import UNARY_OPS


def try_fold_unit_expr_as_single_mu(node: ast.AST) -> ir.MathNode | None:
    """
    遍历乘除法表达式树，提取出其中的单位及其幂次，
    构造一个单一的 ir.Mu 节点表示该单位表达式。
    若没有符合的单位乘除法表达式，返回 None。
    """
    if not isinstance(node, ast.BinOp) or not isinstance(
        node.op, (ast.Mult, ast.Div, ast.Pow)
    ):
        return None

    # 使用辅助类来管理状态
    collector = UnitExpressionCollector()
    if not collector.walk(node, +1) or not collector.unit_powers:
        return None

    # 构建单位节点（只包含单位部分，不包含系数）
    units = unit.parse_units(unit_powers_to_expr(collector.unit_powers))
    return ir.mu(str(units))


def extract_numeric_part(node: ast.AST) -> ir.MathNode | None:
    """从单位混合表达式中提取纯数值部分。"""
    if not isinstance(node, ast.BinOp):
        return None
    return _extract(node)


def _is_unit_node(node: ast.AST) -> bool:
    """检查是否为单位相关节点。"""
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "unit"
    ):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
        return _is_unit_node(node.left)
    return False


def _extract(node: ast.AST) -> ir.MathNode | None:
    """递归提取数值部分。"""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return ir.mn(node.value)

    if isinstance(node, ast.UnaryOp):
        # 处理带符号的数值（如 -15）
        # 如果操作数是常量，直接应用符号到数值
        if isinstance(node.operand, ast.Constant) and isinstance(
            node.operand.value, (int, float)
        ):
            if isinstance(node.op, ast.USub):
                return ir.mn(-node.operand.value)
            if isinstance(node.op, ast.UAdd):
                return ir.mn(node.operand.value)

        # 对于更复杂的表达式，递归提取
        operand = _extract(node.operand)
        if operand is not None:
            symbol = UNARY_OPS.get(type(node.op), "")
            return ir.mrow([ir.mo(symbol), operand])
        return None

    if _is_unit_node(node):
        return None

    if isinstance(node, ast.BinOp):
        left, right = _extract(node.left), _extract(node.right)
        if left and right:
            if isinstance(node.op, ast.Mult):
                return ir.mrow([left, ir.mo("·"), right])
            return ir.mfrac(left, right)
        return left or right

    return None
