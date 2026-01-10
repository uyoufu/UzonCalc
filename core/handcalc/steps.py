from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

import pint

from core.context import CalcContext
from core.handcalc import ir
from core.handcalc.transformers import transform_ir


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
    """Render a text paragraph.

    If `value` is provided at runtime, it wins (used by f-strings).
    """

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

        output = value if value is not None else self.text
        ctx.append_content(f"<p>{html.escape(str(output))}</p>")


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

        locals_map = locals_map or {}

        expr_node: ir.MathNode = self.expr or ir.mtext("")
        parts: list[ir.MathNode] = [expr_node]
        parts = _maybe_add_substitution(ctx, parts, expr_node, locals_map)
        parts = _maybe_add_value(parts, value)
        ctx.append_content(f"<p>{ir.equation(parts).to_mathml_xml()}</p>")


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

        lhs: ir.MathNode = self.lhs or ir.mtext("")
        rhs = self.rhs

        # Private assignment suppression: only when lhs is a simple variable.
        if _is_private_lhs(lhs) and ctx.options.suppress_private_assignments:
            return

        locals_map = locals_map or {}

        parts: list[ir.MathNode] = [lhs]
        if rhs is not None:
            parts.append(rhs)
            parts = _maybe_add_substitution(ctx, parts, rhs, locals_map)

        parts = _maybe_add_value(parts, value)
        ctx.append_content(f"<p>{ir.equation(parts).to_mathml_xml()}</p>")


def _maybe_add_value(parts: list[ir.MathNode], value: Any) -> list[ir.MathNode]:
    if value is None:
        return parts
    value_ir = value_to_ir(value)
    if value_ir not in parts:
        parts.append(value_ir)
    return parts


def _maybe_add_substitution(
    ctx: CalcContext,
    parts: list[ir.MathNode],
    expr_node: ir.MathNode,
    locals_map: Mapping[str, Any],
) -> list[ir.MathNode]:
    if not ctx.options.enable_substitution:
        return parts

    substituted = substitute_vars(expr_node, locals_map)
    if substituted != expr_node:
        parts.append(substituted)
    return parts


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
