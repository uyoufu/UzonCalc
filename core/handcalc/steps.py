from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

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
class FStringStep:
    """Render an f-string as mixed text + inline equations."""

    segments: list[Any]

    def _render_math(
        self,
        expr_desc: Mapping[str, Any],
        locals_map: Mapping[str, Any],
    ) -> str:
        kind = expr_desc.get("kind")
        value_var = expr_desc.get("value_var", "")
        runtime_value = locals_map.get(value_var) if value_var else None

        if kind == "namedexpr":
            lhs: ir.MathNode = expr_desc.get("lhs") or ir.mtext("")
            rhs: ir.MathNode = expr_desc.get("rhs") or ir.mtext("")
            parts: list[ir.MathNode] = [lhs] + _build_equation_parts(
                rhs, locals_map, runtime_value
            )
            return ir.equation(parts).to_mathml_xml()

        expr_node: ir.MathNode = expr_desc.get("expr") or ir.mtext("")
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
                self._render_math(seg, locals_map)
                if isinstance(seg, Mapping)
                else html.escape(seg if isinstance(seg, str) else str(seg))
            )
            for seg in self.segments
        ]
        _render_html(ctx, "".join(out_parts))
