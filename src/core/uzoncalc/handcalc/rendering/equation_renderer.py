from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from .. import ir
from ..transformers import transform_ir
from .value_renderer import is_array_value, should_render_runtime_value, value_to_ir

SYMBOL_COLON = ":"
SYMBOL_COMMA = ","


def build_equation_parts(
    expr_node: ir.MathNode,
    locals_map: Mapping[str, Any],
    value: Any,
    *,
    enable_substitution: bool = True,
) -> list[ir.MathNode]:
    """构建方程的各部分（表达式、替换值、结果值）。"""
    expr_node = style_array_vars(expr_node, locals_map)
    parts: list[ir.MathNode] = [expr_node]

    if enable_substitution:
        # 仅替换公式中的变量节点，不直接展示复杂运行期对象 repr。
        substituted = substitute_vars(expr_node, locals_map)
        if substituted != expr_node:
            parts.append(substituted)

    if should_render_runtime_value(value):
        value_ir = value_to_ir(value)
        if value_ir not in parts:
            parts.append(value_ir)
    return parts


def prepare_lhs(
    lhs: ir.MathNode, value: Any, locals_map: Mapping[str, Any]
) -> ir.MathNode:
    """准备左侧表达式，处理数组变量样式。"""
    lhs = lhs or ir.mtext("")
    if isinstance(lhs, ir.Mi):
        if is_array_value(value) or is_array_value(locals_map.get(lhs.name)):
            lhs = ir.mi_array(lhs.name)
    return style_array_vars(lhs, locals_map)


def build_equation_parts_for_assignment(
    lhs: ir.MathNode,
    rhs: ir.MathNode | None,
    value: Any,
    locals_map: Mapping[str, Any],
    *,
    enable_substitution: bool = True,
) -> list[ir.MathNode]:
    """为赋值语句构建方程各部分。"""
    parts: list[ir.MathNode] = [lhs]
    if rhs is not None:
        rhs_styled = style_array_vars(rhs, locals_map)
        parts.extend(
            build_equation_parts(
                rhs_styled,
                locals_map,
                value,
                enable_substitution=enable_substitution,
            )[1:]
        )
        parts.insert(1, rhs_styled)
    elif should_render_runtime_value(value):
        parts.append(value_to_ir(value))
    return parts


def substitute_vars(node: ir.MathNode, locals_map: Mapping[str, Any]) -> ir.MathNode:
    """Replace variables with runtime values when available (conservative)."""

    def _repl(n: ir.MathNode) -> ir.MathNode | None:
        resolved = _try_resolve_subscript(n, locals_map)
        if resolved is not None:
            return resolved

        if isinstance(n, ir.Mi) and n.name in locals_map:
            return value_to_ir(locals_map[n.name])

        return None

    return transform_ir(
        node,
        _repl,
        should_descend=lambda parent, field_name: not (
            isinstance(parent, ir.MSub) and field_name == "base"
        ),
    )


def style_array_vars(node: ir.MathNode, locals_map: Mapping[str, Any]) -> ir.MathNode:
    """将数组变量渲染为数组样式 MathIR。"""

    def _repl(n: ir.MathNode) -> ir.MathNode | None:
        if isinstance(n, ir.Mi) and not isinstance(n, ir.MiArray):
            if is_array_value(locals_map.get(n.name)):
                return ir.mi_array(n.name)
        return None

    return transform_ir(node, _repl)


def is_private_lhs(lhs: Any) -> bool:
    """判断赋值左侧是否为默认隐藏的私有变量。"""
    return isinstance(lhs, ir.Mi) and lhs.name.startswith("_")


def _try_resolve_subscript(
    node: ir.MathNode, locals_map: Mapping[str, Any]
) -> ir.MathNode | None:
    if not isinstance(node, ir.MSub):
        return None

    base = node.base
    if not isinstance(base, ir.Mi):
        return None

    base_value = locals_map.get(base.name)
    if base_value is None or not isinstance(base_value, (list, tuple, np.ndarray, dict)):
        return None

    index = _ir_to_index(node.subscript, locals_map)
    if index is None:
        return None

    try:
        return value_to_ir(base_value[index])
    except Exception:
        return None


def _ir_to_index(node: ir.MathNode, locals_map: Mapping[str, Any]) -> Any | None:
    """将 IR 节点转换为索引值。"""
    if isinstance(node, ir.Mn):
        return _parse_number(node.value)
    if isinstance(node, ir.Mi):
        return locals_map.get(node.name)
    if isinstance(node, ir.MText):
        return node.text
    if isinstance(node, ir.MRow):
        return _parse_mrow_index(node.children, locals_map)
    return None


def _parse_number(text: str) -> int | float | None:
    try:
        num = float(text)
    except Exception:
        return None
    return int(num) if num.is_integer() else num


def _parse_mrow_index(
    children: list[ir.MathNode], locals_map: Mapping[str, Any]
) -> Any | None:
    """解析 MRow 节点为索引值（切片、元组或单个值）。"""
    if _has_symbol(children, SYMBOL_COLON):
        return _parse_slice(children, locals_map)

    if _has_symbol(children, SYMBOL_COMMA):
        parts = _split_on_symbol(children, SYMBOL_COMMA)
        items = [_nodes_to_index(part, locals_map) for part in parts]
        if any(item is None for item in items):
            return None
        return tuple(items)

    if len(children) == 1:
        return _ir_to_index(children[0], locals_map)
    return None


def _has_symbol(children: list[ir.MathNode], symbol: str) -> bool:
    """检查子节点列表中是否包含指定符号。"""
    return any(isinstance(ch, ir.Mo) and ch.symbol == symbol for ch in children)


def _split_on_symbol(
    children: list[ir.MathNode], symbol: str
) -> list[list[ir.MathNode]]:
    """按指定符号分割子节点列表。"""
    parts: list[list[ir.MathNode]] = [[]]
    for ch in children:
        if isinstance(ch, ir.Mo) and ch.symbol == symbol:
            parts.append([])
        else:
            parts[-1].append(ch)
    return parts


def _nodes_to_index(
    nodes: list[ir.MathNode], locals_map: Mapping[str, Any]
) -> Any | None:
    if not nodes:
        return None
    if len(nodes) == 1:
        return _ir_to_index(nodes[0], locals_map)
    return _ir_to_index(ir.mrow(nodes), locals_map)


def _parse_slice(
    children: list[ir.MathNode], locals_map: Mapping[str, Any]
) -> slice | None:
    """解析切片表达式。"""
    parts = _split_on_symbol(children, SYMBOL_COLON)
    if not (2 <= len(parts) <= 3):
        return None

    lower = _nodes_to_index(parts[0], locals_map)
    upper = _nodes_to_index(parts[1], locals_map)
    step = _nodes_to_index(parts[2], locals_map) if len(parts) == 3 else None
    return slice(lower, upper, step)
