from __future__ import annotations

import ast
from collections.abc import Callable
from dataclasses import dataclass

from ...units import unit
from .. import ir
from ..unit_collector import (
    UnitExpressionCollector,
    get_const_number,
    unit_powers_to_expr,
)
from .operator_rendering import UNARY_OPS

ExprConverter = Callable[[ast.AST], ir.MathNode]


@dataclass(slots=True)
class MixedUnitExpressionParts:
    """单位混合表达式拆分结果。"""

    unit_powers: dict[str, float]
    numerator_nodes: list[ast.AST]
    denominator_nodes: list[ast.AST]


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


def try_fold_mixed_unit_expr(
    node: ast.AST, *, expr_to_ir: ExprConverter
) -> ir.MathNode | None:
    """将含非单位因子的单位表达式折叠为“数值部分 + 单一单位”。"""
    parts = split_mixed_unit_expression(node)
    if parts is None:
        return None

    units = unit.parse_units(unit_powers_to_expr(parts.unit_powers))
    unit_node = ir.mu(str(units))
    numeric_node = build_non_unit_node(parts, expr_to_ir=expr_to_ir)
    if numeric_node is None:
        return unit_node
    return ir.mrow([numeric_node, ir.mo(""), unit_node])


def split_mixed_unit_expression(node: ast.AST) -> MixedUnitExpressionParts | None:
    """拆分乘除表达式中的单位因子和非单位因子。"""
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, (ast.Mult, ast.Div)):
        return None

    parts = MixedUnitExpressionParts(
        unit_powers={}, numerator_nodes=[], denominator_nodes=[]
    )
    if not collect_mixed_unit_parts(node, +1, parts) or not parts.unit_powers:
        return None
    return parts


def collect_mixed_unit_parts(
    node: ast.AST, sign: int, parts: MixedUnitExpressionParts
) -> bool:
    """递归收集单位幂次，并按乘除方向保留非单位因子。"""
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Mult):
            return collect_mixed_unit_parts(
                node.left, sign, parts
            ) and collect_mixed_unit_parts(node.right, sign, parts)
        if isinstance(node.op, ast.Div):
            return collect_mixed_unit_parts(
                node.left, sign, parts
            ) and collect_mixed_unit_parts(node.right, -sign, parts)

    if _is_unit_node(node):
        unit_name, power = unit_node_to_power(node)
        if unit_name is None or power is None:
            return False
        add_unit_power(parts.unit_powers, unit_name, float(sign) * power)
        return True

    # 非单位因子按分子/分母方向保存，后续交给通用表达式渲染器。
    target_nodes = parts.numerator_nodes if sign == 1 else parts.denominator_nodes
    target_nodes.append(node)
    return True


def unit_node_to_power(node: ast.AST) -> tuple[str | None, float | None]:
    """读取 unit.xxx 或 unit.xxx**n 对应的单位名称和幂次。"""
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "unit"
    ):
        return node.attr, 1.0
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
        if not (
            isinstance(node.left, ast.Attribute)
            and isinstance(node.left.value, ast.Name)
            and node.left.value.id == "unit"
        ):
            return None, None
        power = get_const_number(node.right)
        if power is None:
            return None, None
        return node.left.attr, float(power)
    return None, None


def add_unit_power(unit_powers: dict[str, float], name: str, power: float) -> None:
    """累加单位幂次，幂次归零时移除该单位。"""
    new_power = unit_powers.get(name, 0.0) + power
    if abs(new_power) < 1e-12:
        unit_powers.pop(name, None)
    else:
        unit_powers[name] = new_power


def build_non_unit_node(
    parts: MixedUnitExpressionParts, *, expr_to_ir: ExprConverter
) -> ir.MathNode | None:
    """根据拆分出的非单位分子分母构造 MathIR。"""
    numerator = build_factor_product(parts.numerator_nodes, expr_to_ir=expr_to_ir)
    denominator = build_factor_product(parts.denominator_nodes, expr_to_ir=expr_to_ir)

    if denominator is None:
        return numerator

    return ir.mfrac(numerator or ir.mn(1), denominator)


def build_factor_product(
    nodes: list[ast.AST], *, expr_to_ir: ExprConverter
) -> ir.MathNode | None:
    """将多个非单位因子渲染为乘积。"""
    if not nodes:
        return None

    children: list[ir.MathNode] = []
    for idx, factor_node in enumerate(nodes):
        if idx:
            children.append(ir.mo("·"))
        children.append(expr_to_ir(factor_node))

    if len(children) == 1:
        return children[0]
    return ir.mrow(children)


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
