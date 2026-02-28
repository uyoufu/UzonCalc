from __future__ import annotations

import html
from dataclasses import dataclass, fields, is_dataclass, replace
from typing import Any, Literal, Mapping, Protocol

import pint

from ..context import CalcContext
from . import ir
from .transformers import transform_ir
import numpy as np

# 常量定义
FLOAT_PRECISION = 12  # 浮点数清理精度
FLOAT_FORMAT_PRECISION = 15  # 浮点数格式化精度
SYMBOL_COLON = ":"
SYMBOL_COMMA = ","
SYMBOL_LEFT_BRACKET = "["
SYMBOL_RIGHT_BRACKET = "]"
HTML_TAG_SPAN = "span"
HTML_TAG_P = "p"


def _render_html(ctx: CalcContext, content: str) -> None:
    """通用 HTML 渲染辅助函数"""
    tag = HTML_TAG_SPAN if ctx.is_inline_mode else HTML_TAG_P
    ctx.append_content(f"<{tag}>{content}</{tag}>")


class Step(Protocol):
    def record(
        self,
        ctx: CalcContext,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class TextStep:
    """Render a text paragraph."""

    text: str = ""

    def record(
        self,
        ctx: CalcContext,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> None:
        if ctx.options.skip_content:
            return
        content = str(value if value is not None else self.text)
        _render_html(ctx, html.escape(content))


def _build_equation_parts(
    expr_node: ir.MathNode,
    locals_map: Mapping[str, Any],
    value: Any,
) -> list[ir.MathNode]:
    """构建方程的各部分（表达式、替换、结果值）"""
    expr_node = _style_array_vars(expr_node, locals_map)
    parts: list[ir.MathNode] = [expr_node]
    substituted = substitute_vars(expr_node, locals_map)
    if substituted != expr_node:
        parts.append(substituted)
    if value is not None:
        value_ir = value_to_ir(value)
        if value_ir not in parts:
            parts.append(value_ir)
    return parts


def _prepare_lhs(
    lhs: ir.MathNode, value: Any, locals_map: Mapping[str, Any]
) -> ir.MathNode:
    """准备左侧表达式，处理数组变量样式"""
    lhs = lhs or ir.mtext("")
    if isinstance(lhs, ir.Mi):
        if _is_array_value(value) or _is_array_value(locals_map.get(lhs.name)):
            lhs = ir.mi_array(lhs.name)
    return _style_array_vars(lhs, locals_map)


def _build_equation_parts_for_assignment(
    lhs: ir.MathNode,
    rhs: ir.MathNode | None,
    value: Any,
    locals_map: Mapping[str, Any],
) -> list[ir.MathNode]:
    """为赋值语句构建方程各部分"""
    parts: list[ir.MathNode] = [lhs]
    if rhs is not None:
        rhs_styled = _style_array_vars(rhs, locals_map)
        parts.extend(_build_equation_parts(rhs_styled, locals_map, value)[1:])
        parts.insert(1, rhs_styled)
    elif value is not None:
        parts.append(value_to_ir(value))
    return parts


@dataclass(frozen=True, slots=True)
class ExprStep:
    expr: ir.MathNode

    def record(
        self,
        ctx: CalcContext,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> None:
        if ctx.options.skip_content:
            return
        expr_node = self.expr or ir.mtext("")
        parts = _build_equation_parts(expr_node, locals_map or {}, value)
        _render_html(ctx, ir.equation(parts).to_mathml_xml())


@dataclass(frozen=True, slots=True)
class EquationStep:
    lhs: ir.MathNode
    rhs: ir.MathNode | None

    def record(
        self,
        ctx: CalcContext,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> None:
        if ctx.options.skip_content:
            return

        locals_map = locals_map or {}
        lhs = _prepare_lhs(self.lhs, value, locals_map)

        if _is_private_lhs(lhs) and ctx.options.suppress_private_assignments:
            return

        parts = _build_equation_parts_for_assignment(lhs, self.rhs, value, locals_map)
        _render_html(ctx, ir.equation(parts).to_mathml_xml())


def substitute_vars(node: ir.MathNode, locals_map: Mapping[str, Any]) -> ir.MathNode:
    """Replace variables with runtime values when available (conservative)."""

    def _walk(n: ir.MathNode) -> ir.MathNode:
        resolved = _try_resolve_subscript(n, locals_map)
        if resolved is not None:
            return resolved

        if isinstance(n, ir.Mi) and n.name in locals_map:
            return value_to_ir(locals_map[n.name])

        if not is_dataclass(n):
            return n

        updated, changed = _update_node_fields(n, _walk)
        if not changed:
            return n

        try:
            return replace(n, **updated)  # type: ignore[return-value]
        except Exception:
            return n

    return _walk(node)


def _update_node_fields(node: ir.MathNode, transform_fn) -> tuple[dict[str, Any], bool]:
    """更新数据类节点的字段，返回更新后的字段字典和是否有变化的标志"""
    updated: dict[str, Any] = {}
    changed = False

    for f in fields(node):
        v = getattr(node, f.name)

        # 处理单个 MathNode 字段
        if isinstance(v, ir.MathNode):
            # MSub 的 base 字段不进行替换
            if isinstance(node, ir.MSub) and f.name == "base":
                new_v = v
            else:
                new_v = transform_fn(v)
            updated[f.name] = new_v
            changed = changed or (new_v is not v)
            continue

        # 处理 MathNode 列表字段
        if isinstance(v, list) and all(isinstance(ch, ir.MathNode) for ch in v):
            new_list = [transform_fn(ch) for ch in v]
            updated[f.name] = new_list
            changed = changed or any(nv is not ov for nv, ov in zip(new_list, v))
            continue

        # 其他字段保持不变
        updated[f.name] = v

    return updated, changed


def _try_resolve_subscript(
    node: ir.MathNode, locals_map: Mapping[str, Any]
) -> ir.MathNode | None:
    if not isinstance(node, ir.MSub):
        return None

    base = node.base
    if not isinstance(base, ir.Mi):
        return None

    base_value = locals_map.get(base.name)
    if base_value is None:
        return None

    if not isinstance(base_value, (list, tuple, np.ndarray, dict)):
        return None

    index = _ir_to_index(node.subscript, locals_map)
    if index is None:
        return None

    try:
        return value_to_ir(base_value[index])
    except Exception:
        return None


def _ir_to_index(node: ir.MathNode, locals_map: Mapping[str, Any]) -> Any | None:
    """将 IR 节点转换为索引值"""
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
    if num.is_integer():
        return int(num)
    return num


def _parse_mrow_index(
    children: list[ir.MathNode], locals_map: Mapping[str, Any]
) -> Any | None:
    """解析 MRow 节点为索引值（切片、元组或单个值）"""
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
    """检查子节点列表中是否包含指定符号"""
    return any(isinstance(ch, ir.Mo) and ch.symbol == symbol for ch in children)


def _split_on_symbol(
    children: list[ir.MathNode], symbol: str
) -> list[list[ir.MathNode]]:
    """按指定符号分割子节点列表"""
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
    """解析切片表达式"""
    parts = _split_on_symbol(children, SYMBOL_COLON)
    if not (2 <= len(parts) <= 3):
        return None

    lower = _nodes_to_index(parts[0], locals_map)
    upper = _nodes_to_index(parts[1], locals_map)
    step = _nodes_to_index(parts[2], locals_map) if len(parts) == 3 else None
    return slice(lower, upper, step)


def _is_array_value(value: Any) -> bool:
    if isinstance(
        value,
        (list, tuple, np.ndarray),
    ):
        return True
    return False


def _style_array_vars(node: ir.MathNode, locals_map: Mapping[str, Any]) -> ir.MathNode:
    def _repl(n: ir.MathNode) -> ir.MathNode | None:
        if isinstance(n, ir.Mi) and not isinstance(n, ir.MiArray):
            if _is_array_value(locals_map.get(n.name)):
                return ir.mi_array(n.name)
        return None

    return transform_ir(node, _repl)


def value_to_ir(value: Any) -> ir.MathNode:
    # Numbers
    if isinstance(value, (int, float)):
        return ir.mn(_format_number(value))

    # Strings
    if isinstance(value, str):
        return ir.mtext(value)

    if isinstance(
        value,
        (list, tuple),
    ):
        items: list[ir.MathNode] = []
        for idx, item in enumerate(value):
            if idx:
                items.append(ir.mo(SYMBOL_COMMA))
            items.append(value_to_ir(item))
        return ir.mrow_array(
            [ir.mo(SYMBOL_LEFT_BRACKET), *items, ir.mo(SYMBOL_RIGHT_BRACKET)]
        )

    if isinstance(value, np.ndarray):
        return value_to_ir(value.tolist())

    if isinstance(value, pint.Quantity):
        # 使用 _format_number 处理浮点数精度问题
        magnitude = value.magnitude
        if isinstance(magnitude, (int, float)):
            formatted_magnitude = _format_number(magnitude)
        else:
            formatted_magnitude = str(magnitude)
        return ir.mrow([ir.mn(formatted_magnitude), ir.mo(""), ir.mu(str(value.units))])

    return ir.mtext(str(value))


def _clean_float(value: float, precision: int = FLOAT_PRECISION) -> float:
    """清理浮点数精度问题"""
    # 使用 round 移除浮点数运算误差
    return round(value, precision)


def _format_number(value: float | int) -> str:
    """格式化数字，移除不必要的小数点和尾随零"""
    if isinstance(value, int):
        return str(value)

    # 清理浮点数精度问题
    cleaned = _clean_float(value)

    # 如果是整数值，不显示小数部分
    if cleaned == int(cleaned):
        return str(int(cleaned))

    # 格式化为字符串并移除尾随零
    return f"{cleaned:.{FLOAT_FORMAT_PRECISION}g}"


def _is_private_lhs(lhs: Any) -> bool:
    return isinstance(lhs, ir.Mi) and lhs.name.startswith("_")


@dataclass(frozen=True, slots=True)
class FStringSegment:
    """f-string 的一个片段（文本或表达式）"""

    kind: Literal["text", "expr", "namedexpr"]

    # For kind="text"
    text: str = ""

    # For kind="expr"
    expr: ir.MathNode | None = None

    # For kind="namedexpr"
    lhs: ir.MathNode | None = None
    rhs: ir.MathNode | None = None

    # For kind="expr" and kind="namedexpr"
    value_var: str = ""
    format_spec: str = ""  # 格式化规范，如 ".3f"


@dataclass(frozen=True, slots=True)
class FStringStep:
    """Render an f-string as mixed text + inline equations."""

    segments: list[FStringSegment]

    def _render_math(
        self,
        segment: FStringSegment,
        locals_map: Mapping[str, Any],
        ctx: CalcContext,
    ) -> str:
        """渲染数学表达式片段"""
        runtime_value = locals_map.get(segment.value_var) if segment.value_var else None
        runtime_value = _apply_format_spec(runtime_value, segment.format_spec)

        # 如果 enable_fstring_equation 为 False，只显示值
        if not ctx.options.enable_fstring_equation:
            return _render_value_only(runtime_value)

        if segment.kind == "namedexpr":
            return _render_namedexpr(segment, runtime_value, locals_map)

        return _render_expr(segment, runtime_value, locals_map)

    def record(
        self,
        ctx: CalcContext,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> None:
        if ctx.options.skip_content:
            return
        locals_map = locals_map or {}
        out_parts = [
            (
                self._render_math(seg, locals_map, ctx)
                if seg.kind in ("expr", "namedexpr")
                else html.escape(seg.text)
            )
            for seg in self.segments
        ]
        _render_html(ctx, "".join(out_parts))


def _apply_format_spec(value: Any, format_spec: str) -> Any:
    """应用格式化规范到值"""
    if not format_spec or value is None:
        return value

    import pint

    if isinstance(value, pint.Quantity):
        # 分别格式化数值和单位
        formatted_magnitude = format(value.magnitude, format_spec)
        return ir.mrow(
            [
                ir.mn(formatted_magnitude),
                ir.mo(""),
                ir.mu(str(value.units)),
            ]
        )
    else:
        # 对于非 Quantity 值，直接格式化
        formatted_value = format(value, format_spec)
        return value_to_ir(formatted_value)


def _render_value_only(value: Any) -> str:
    """仅渲染值（不显示表达式），直接返回字符串，不包裹 math"""
    if value is None:
        return ""

    # 直接将值转换为字符串
    if isinstance(value, str):
        return html.escape(value)

    if isinstance(value, pint.Quantity):
        # 对于 Quantity，显示数值和单位
        return html.escape(f"{value.magnitude} {value.units}")

    # 对于其他类型，直接转字符串
    return html.escape(str(value))


def _render_namedexpr(
    segment: FStringSegment, value: Any, locals_map: Mapping[str, Any]
) -> str:
    """渲染命名表达式"""
    lhs: ir.MathNode = segment.lhs or ir.mtext("")
    rhs: ir.MathNode = segment.rhs or ir.mtext("")

    if isinstance(lhs, ir.Mi) and _is_array_value(value):
        lhs = ir.mi_array(lhs.name)

    lhs = _style_array_vars(lhs, locals_map)
    rhs = _style_array_vars(rhs, locals_map)

    # 如果 value 已经是 MathNode，直接使用
    if isinstance(value, ir.MathNode):
        parts: list[ir.MathNode] = [lhs, rhs, value]
    else:
        parts = [lhs] + _build_equation_parts(rhs, locals_map, value)

    return ir.equation(parts).to_mathml_xml()


def _render_expr(
    segment: FStringSegment, value: Any, locals_map: Mapping[str, Any]
) -> str:
    """渲染表达式"""
    expr_node: ir.MathNode = segment.expr or ir.mtext("")
    expr_node = _style_array_vars(expr_node, locals_map)

    # 如果 value 已经是 MathNode，直接使用
    if isinstance(value, ir.MathNode):
        parts = [expr_node, value]
    else:
        parts = _build_equation_parts(expr_node, locals_map, value)

    return ir.equation(parts).to_mathml_xml()
