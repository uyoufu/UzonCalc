from __future__ import annotations

from typing import Any, Mapping

from .. import ir
from ..transformers import transform_ir
from .value_renderer import is_array_value, should_render_runtime_value, value_to_ir

SYMBOL_COLON = ":"
SYMBOL_COMMA = ","
SYMBOL_ATTRIBUTE_SEPARATOR = "."
_UNRESOLVED = object()


def build_equation_parts(
    expr_node: ir.MathNode,
    locals_map: Mapping[str, Any],
    value: Any,
    *,
    enable_formula_expression: bool = True,
    enable_substitution: bool = True,
) -> list[ir.MathNode]:
    """构建方程的各部分（表达式、替换值、结果值）。"""
    expr_node = style_array_vars(expr_node, locals_map)
    parts: list[ir.MathNode] = []
    if enable_formula_expression:
        parts.append(expr_node)

    if enable_substitution:
        # 仅替换公式中的变量节点，不直接展示复杂运行期对象 repr。
        substituted = substitute_vars(
            expr_node,
            locals_map,
            resolve_subscript_values=not should_render_runtime_value(value),
        )
        if substituted != expr_node and substituted not in parts:
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
    enable_formula_expression: bool = True,
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
                enable_formula_expression=enable_formula_expression,
                enable_substitution=enable_substitution,
            )
        )
    elif should_render_runtime_value(value):
        parts.append(value_to_ir(value))
    return parts


def substitute_vars(
    node: ir.MathNode,
    locals_map: Mapping[str, Any],
    *,
    resolve_subscript_values: bool = True,
) -> ir.MathNode:
    """Replace renderable value-position variables with runtime values.

    Args:
        node: MathIR expression to transform.
        locals_map: Runtime local variables captured from the calculation frame.
        resolve_subscript_values: Whether a whole subscript expression may be
            evaluated to its final runtime element.

    Returns:
        A transformed MathIR expression.

    Raises:
        No exceptions are intentionally raised; unsafe substitutions are skipped.
    """

    def _repl(n: ir.MathNode) -> ir.MathNode | None:
        resolved = (
            _try_resolve_subscript(n, locals_map)
            if resolve_subscript_values
            else None
        )
        if resolved is not None:
            return resolved

        if isinstance(n, ir.Mi) and n.name in locals_map:
            value = locals_map[n.name]
            if should_render_runtime_value(value):
                return value_to_ir(value)
            return None

        if isinstance(n, ir.Mi):
            attribute_value = _try_resolve_attribute_path(n.name, locals_map)
            if (
                attribute_value is not _UNRESOLVED
                and should_render_runtime_value(attribute_value)
            ):
                return value_to_ir(attribute_value)

        return None

    return transform_ir(
        node,
        _repl,
        should_descend=lambda parent, field_name: not (
            isinstance(parent, ir.MSub) and field_name == "base"
        ),
        should_descend_child=_should_descend_substitution_child,
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


def _try_resolve_attribute_path(name: str, locals_map: Mapping[str, Any]) -> Any:
    """按 locals 中的根对象解析属性访问路径，失败时返回未解析标记。"""
    if SYMBOL_ATTRIBUTE_SEPARATOR not in name:
        return _UNRESOLVED

    root_name, *attribute_names = name.split(SYMBOL_ATTRIBUTE_SEPARATOR)
    if not root_name or not attribute_names or root_name not in locals_map:
        return _UNRESOLVED

    current_value = locals_map[root_name]
    for attribute_name in attribute_names:
        if not attribute_name:
            return _UNRESOLVED
        try:
            current_value = getattr(current_value, attribute_name)
        except AttributeError:
            return _UNRESOLVED
    return current_value


def _try_resolve_subscript(
    node: ir.MathNode, locals_map: Mapping[str, Any]
) -> ir.MathNode | None:
    if not isinstance(node, ir.MSub):
        return None

    base = node.base
    if not isinstance(base, ir.Mi):
        return None

    base_value = locals_map.get(base.name)
    if base_value is None or not _is_subscriptable_value(base_value):
        return None

    index = _ir_to_index(node.subscript, locals_map)
    if index is None:
        return None

    try:
        value = base_value[index]
    except Exception:
        return None
    if not should_render_runtime_value(value):
        return None
    return value_to_ir(value)


def _should_descend_substitution_child(
    parent: ir.MathNode, field_name: str, child: ir.MathNode, child_index: int
) -> bool:
    """Return whether a child is in a value-position substitution context.

    Args:
        parent: Parent MathIR node.
        field_name: Dataclass field that owns the child.
        child: Child MathIR node.
        child_index: Child index inside the owning list field.

    Returns:
        ``False`` for function/method call targets; otherwise ``True``.

    Raises:
        No exceptions are raised.
    """
    if isinstance(parent, ir.MCall) and field_name == "children" and child_index == 0:
        return False
    return True


def _is_subscriptable_value(value: Any) -> bool:
    """Return True when a runtime value supports safe subscript attempts.

    Args:
        value: Runtime value used as a subscript base.

    Returns:
        Whether the value exposes ``__getitem__``.

    Raises:
        No exceptions are raised.
    """
    return hasattr(value, "__getitem__")


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
