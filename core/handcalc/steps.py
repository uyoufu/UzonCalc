from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Protocol

import pint

from core.context import CalcContext
from core.handcalc import ir
from core.handcalc.transformers import transform_ir


def _render_html(ctx: CalcContext, content: str) -> None:
    """通用 HTML 渲染辅助函数"""
    tag = "span" if ctx.is_inline_mode else "p"
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
    parts: list[ir.MathNode] = [expr_node]
    substituted = substitute_vars(expr_node, locals_map)
    if substituted != expr_node:
        parts.append(substituted)
    if value is not None:
        value_ir = value_to_ir(value)
        if value_ir not in parts:
            parts.append(value_ir)
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
        lhs = self.lhs or ir.mtext("")
        if _is_private_lhs(lhs) and ctx.options.suppress_private_assignments:
            return
        parts: list[ir.MathNode] = [lhs]
        if self.rhs is not None:
            parts.extend(_build_equation_parts(self.rhs, locals_map or {}, value)[1:])
            parts.insert(1, self.rhs)
        elif value is not None:
            parts.append(value_to_ir(value))
        _render_html(ctx, ir.equation(parts).to_mathml_xml())


def substitute_vars(node: ir.MathNode, locals_map: Mapping[str, Any]) -> ir.MathNode:
    """Replace <mi>var</mi> with runtime values when available (conservative)."""

    def _repl(n: ir.MathNode) -> ir.MathNode | None:
        if isinstance(n, ir.Mi) and n.name in locals_map:
            return value_to_ir(locals_map[n.name])
        return None

    return transform_ir(node, _repl)


def value_to_ir(value: Any) -> ir.MathNode:
    # Numbers
    if isinstance(value, (int, float)):
        return ir.mn(value)

    # Strings
    if isinstance(value, str):
        return ir.mtext(value)

    if isinstance(value, pint.Quantity):
        return ir.mrow([ir.mn(value.magnitude), ir.mo(""), ir.mu(str(value.units))])

    return ir.mtext(str(value))


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

        # 如果 enable_fstring_equation 为 False，只显示值
        if not ctx.options.enable_fstring_equation:
            if runtime_value is not None:
                value_ir = value_to_ir(runtime_value)
                return ir.equation([value_ir]).to_mathml_xml()
            # 如果没有值，返回空文本
            return ir.equation([ir.mtext("")]).to_mathml_xml()

        if segment.kind == "namedexpr":
            lhs: ir.MathNode = segment.lhs or ir.mtext("")
            rhs: ir.MathNode = segment.rhs or ir.mtext("")
            parts: list[ir.MathNode] = [lhs] + _build_equation_parts(
                rhs, locals_map, runtime_value
            )
            return ir.equation(parts).to_mathml_xml()

        expr_node: ir.MathNode = segment.expr or ir.mtext("")
        parts = _build_equation_parts(expr_node, locals_map, runtime_value)
        return ir.equation(parts).to_mathml_xml()

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
