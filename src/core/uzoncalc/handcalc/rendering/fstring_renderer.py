from __future__ import annotations

import html
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from ...context import CalcContext
from .. import ir
from .equation_renderer import build_equation_parts, style_array_vars
from .value_renderer import (
    format_runtime_value,
    is_array_value,
    render_html_fragment,
    render_value_fragment,
)


class FStringSegmentLike(Protocol):
    @property
    def kind(self) -> str:
        """Return the segment discriminator."""
        ...

    @property
    def text(self) -> str:
        """Return literal segment text."""
        ...

    @property
    def expr(self) -> ir.MathNode | None:
        """Return the expression node when present."""
        ...

    @property
    def lhs(self) -> ir.MathNode | None:
        """Return the named-expression left side when present."""
        ...

    @property
    def rhs(self) -> ir.MathNode | None:
        """Return the named-expression right side when present."""
        ...

    @property
    def value_var(self) -> str:
        """Return the runtime capture variable name."""
        ...

    @property
    def format_spec(self) -> str:
        """Return the original f-string format specification."""
        ...


def render_fstring_segments(
    segments: Sequence[FStringSegmentLike],
    ctx: CalcContext,
    locals_map: Mapping[str, Any],
) -> str:
    """渲染 f-string 的文本与公式片段。"""
    out_parts = [
        (
            _render_math(seg, locals_map, ctx)
            if seg.kind in ("expr", "namedexpr")
            else html.escape(seg.text)
        )
        for seg in segments
    ]
    return "".join(out_parts)


def _render_math(
    segment: FStringSegmentLike,
    locals_map: Mapping[str, Any],
    ctx: CalcContext,
) -> str:
    runtime_value = locals_map.get(segment.value_var) if segment.value_var else None
    runtime_value = format_runtime_value(runtime_value, segment.format_spec)

    html_fragment = render_html_fragment(runtime_value)
    if html_fragment is not None:
        return html_fragment

    # 如果未启用 f-string 方程，只显示值。
    if not ctx.options.enable_fstring_equation:
        return render_value_fragment(runtime_value)

    if segment.kind == "namedexpr":
        return _render_namedexpr(segment, runtime_value, locals_map, ctx)

    return _render_expr(segment, runtime_value, locals_map, ctx)


def _render_namedexpr(
    segment: FStringSegmentLike,
    value: Any,
    locals_map: Mapping[str, Any],
    ctx: CalcContext,
) -> str:
    """渲染命名表达式。"""
    lhs: ir.MathNode = segment.lhs or ir.mtext("")
    rhs: ir.MathNode = segment.rhs or ir.mtext("")

    if isinstance(lhs, ir.Mi) and is_array_value(value):
        lhs = ir.mi_array(lhs.name)

    lhs = style_array_vars(lhs, locals_map)
    rhs = style_array_vars(rhs, locals_map)

    if isinstance(value, ir.MathNode):
        # 如果 value 已经是 MathNode，直接使用
        parts: list[ir.MathNode] = [lhs]
        if ctx.options.enable_formula_expression:
            parts.append(rhs)
        parts.append(value)
    else:
        parts = [lhs] + build_equation_parts(
            rhs,
            locals_map,
            value,
            enable_formula_expression=ctx.options.enable_formula_expression,
            enable_substitution=True,
        )

    if len(parts) <= 1:
        return render_value_fragment(value)
    return ir.equation(parts).to_mathml_xml()


def _render_expr(
    segment: FStringSegmentLike,
    value: Any,
    locals_map: Mapping[str, Any],
    ctx: CalcContext,
) -> str:
    """渲染数学表达式片段。"""
    expr_node: ir.MathNode = segment.expr or ir.mtext("")
    expr_node = style_array_vars(expr_node, locals_map)

    if isinstance(value, ir.MathNode):
        # 如果 value 已经是 MathNode，直接使用
        parts = [value]
        if ctx.options.enable_formula_expression:
            parts.insert(0, expr_node)
    else:
        parts = build_equation_parts(
            expr_node,
            locals_map,
            value,
            enable_formula_expression=ctx.options.enable_formula_expression,
            enable_substitution=True,
        )

    if not parts:
        return render_value_fragment(value)
    return ir.equation(parts).to_mathml_xml()
