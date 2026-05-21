from __future__ import annotations

import ast
from collections.abc import Callable
from dataclasses import dataclass

from ...units import unit
from .. import ir
from ..unit_collector import get_const_number, unit_powers_to_expr

ExprConverter = Callable[[ast.AST], ir.MathNode]


@dataclass(slots=True)
class UnitExpressionParts:
    """单位表达式拆分结果。"""

    unit_powers: dict[str, float]
    numerator_nodes: list[ast.AST]
    denominator_nodes: list[ast.AST]
    has_unit_factor: bool = False


def try_fold_unit_expr_as_single_mu(node: ast.AST) -> ir.MathNode | None:
    """将纯单位表达式折叠为单一单位节点。"""
    parts = split_unit_expression(node)
    if parts is None or parts.numerator_nodes or parts.denominator_nodes:
        return None

    return build_unit_node(parts.unit_powers)


def try_fold_mixed_unit_expr(
    node: ast.AST, *, expr_to_ir: ExprConverter
) -> ir.MathNode | None:
    """将单位表达式折叠为“非单位部分 + 单一单位”。"""
    parts = split_unit_expression(node)
    if parts is None:
        return None

    unit_node = build_unit_node(parts.unit_powers)
    numeric_node = build_non_unit_node(parts, expr_to_ir=expr_to_ir)
    if unit_node is None:
        # 单位完全抵消时，只保留非单位部分；纯单位抵消显示为 1。
        return numeric_node or ir.mn(1)
    if numeric_node is None:
        return unit_node
    return ir.mrow([numeric_node, ir.mo(""), unit_node])


def split_unit_expression(node: ast.AST) -> UnitExpressionParts | None:
    """拆分乘除幂表达式中的单位因子和非单位因子。"""
    if not isinstance(node, ast.BinOp):
        return None

    parts = UnitExpressionParts(
        unit_powers={}, numerator_nodes=[], denominator_nodes=[]
    )
    if not collect_unit_expression_parts(node, +1.0, parts):
        return None
    if not parts.has_unit_factor:
        return None
    return parts


def collect_unit_expression_parts(
    node: ast.AST, signed_power: float, parts: UnitExpressionParts
) -> bool:
    """递归收集单位幂次，并按分子分母方向保留非单位因子。"""
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Mult):
            return collect_unit_expression_parts(
                node.left, signed_power, parts
            ) and collect_unit_expression_parts(node.right, signed_power, parts)
        if isinstance(node.op, ast.Div):
            return collect_unit_expression_parts(
                node.left, signed_power, parts
            ) and collect_unit_expression_parts(node.right, -signed_power, parts)
        if isinstance(node.op, ast.Pow):
            folded_power = get_const_number(node.right)
            if folded_power is not None:
                return collect_powered_unit_parts(
                    node.left, signed_power, folded_power, parts
                )

    if _is_unit_attribute(node):
        parts.has_unit_factor = True
        add_unit_power(parts.unit_powers, node.attr, signed_power)
        return True

    # 非单位因子按方向保存，后续交给通用表达式渲染器处理。
    append_non_unit_factor(parts, node, signed_power)
    return True


def collect_powered_unit_parts(
    node: ast.AST,
    signed_power: float,
    folded_power: float,
    parts: UnitExpressionParts,
) -> bool:
    """收集整体幂次作用下的单位表达式。"""
    base_parts = UnitExpressionParts(
        unit_powers={}, numerator_nodes=[], denominator_nodes=[]
    )
    if not collect_unit_expression_parts(node, +1.0, base_parts):
        return False
    if not base_parts.has_unit_factor:
        append_non_unit_factor(
            parts,
            ast.BinOp(left=node, op=ast.Pow(), right=ast.Constant(value=folded_power)),
            signed_power,
        )
        return True

    parts.has_unit_factor = True
    for unit_name, unit_power in base_parts.unit_powers.items():
        add_unit_power(
            parts.unit_powers,
            unit_name,
            signed_power * folded_power * unit_power,
        )

    # 整体幂次会同步作用到非单位分子分母因子。
    for factor_node in base_parts.numerator_nodes:
        append_non_unit_factor(parts, factor_node, signed_power * folded_power)
    for factor_node in base_parts.denominator_nodes:
        append_non_unit_factor(parts, factor_node, -signed_power * folded_power)
    return True


def unit_node_to_power(node: ast.AST) -> tuple[str | None, float | None]:
    """读取 unit.xxx 或 unit.xxx**n 对应的单位名称和幂次。"""
    if _is_unit_attribute(node):
        return node.attr, 1.0
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
        if not _is_unit_attribute(node.left):
            return None, None
        power = get_const_number(node.right)
        if power is None:
            return None, None
        return node.left.attr, float(power)
    return None, None


def append_non_unit_factor(
    parts: UnitExpressionParts, node: ast.AST, signed_power: float
) -> None:
    """按幂次方向追加非单位因子。"""
    if abs(signed_power) < 1e-12:
        return

    target_nodes = (
        parts.numerator_nodes if signed_power > 0 else parts.denominator_nodes
    )
    abs_power = abs(signed_power)
    if abs(abs_power - 1.0) < 1e-12:
        target_nodes.append(node)
        return

    # 非单位因子来自整体幂次时，构造等价的幂运算节点交给通用渲染器。
    target_nodes.append(
        ast.BinOp(left=node, op=ast.Pow(), right=ast.Constant(value=abs_power))
    )


def build_unit_node(unit_powers: dict[str, float]) -> ir.MathNode | None:
    """根据单位幂次构造单一单位节点。"""
    if not unit_powers:
        return None

    units = unit.parse_units(unit_powers_to_expr(unit_powers))
    return ir.mu(str(units))


def _is_unit_attribute(node: ast.AST) -> bool:
    """检查是否为 unit.xxx 形式。"""
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "unit"
    )


def add_unit_power(unit_powers: dict[str, float], name: str, power: float) -> None:
    """累加单位幂次，幂次归零时移除该单位。"""
    new_power = unit_powers.get(name, 0.0) + power
    if abs(new_power) < 1e-12:
        unit_powers.pop(name, None)
    else:
        unit_powers[name] = new_power


def build_non_unit_node(
    parts: UnitExpressionParts, *, expr_to_ir: ExprConverter
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
    """从单位混合表达式中提取非单位部分，保留兼容旧调用。"""
    parts = split_unit_expression(node)
    if parts is None:
        return None
    return build_non_unit_node(parts, expr_to_ir=_simple_expr_to_ir)


def _simple_expr_to_ir(node: ast.AST) -> ir.MathNode:
    """将基础非单位节点转换为 MathIR，供兼容提取函数使用。"""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return ir.mn(node.value)
    if isinstance(node, ast.BinOp):
        left = _simple_expr_to_ir(node.left)
        right = _simple_expr_to_ir(node.right)
        if isinstance(node.op, ast.Mult):
            return ir.mrow([left, ir.mo("·"), right])
        if isinstance(node.op, ast.Div):
            return ir.mfrac(left, right)
        if isinstance(node.op, ast.Pow):
            return ir.msup(left, right)
    return ir.mtext(ast.unparse(node))


def split_mixed_unit_expression(node: ast.AST) -> UnitExpressionParts | None:
    """兼容旧名称：拆分单位表达式中的单位因子和非单位因子。"""
    return split_unit_expression(node)


def collect_mixed_unit_parts(
    node: ast.AST, sign: int, parts: UnitExpressionParts
) -> bool:
    """兼容旧名称：递归收集单位幂次和非单位因子。"""
    return collect_unit_expression_parts(node, float(sign), parts)
