from __future__ import annotations

import html
import pint
from typing import Any, Mapping

from core.context import CalcContext

from . import ir
from .mathml_renderer import render_equation


def record_step(
    ctx: CalcContext,
    *,
    step: dict,
    locals_map: Mapping[str, Any] | None = None,
    value: Any = None,
) -> None:
    """Record a structured step.

    step schema (minimal):
    - {"kind":"text", "text": <str>}
    - {"kind":"expr", "expr": <MathNode>}
    - {"kind":"equation", "lhs": <MathNode>, "rhs": <MathNode|None>}

    `locals_map` is used for optional substitution.
    `value` is an optional runtime value to append as the final '= value' part.
    """

    if ctx.options.skip_content:
        return

    kind = step.get("kind")

    if kind == "text":
        text = value if value is not None else step.get("text", "")
        ctx.append_content(f"<p>{html.escape(str(text))}</p>")
        return

    locals_map = locals_map or {}

    if kind == "expr":
        expr_node: ir.Math = step.get("expr") or ir.mtext("")
        parts: list[ir.Math] = [expr_node]
        parts = _maybe_add_substitution(ctx, parts, expr_node, locals_map)
        parts = _maybe_add_value(parts, value)
        ctx.append_content(f"<p>{render_equation(parts)}</p>")
        return

    if kind == "equation":
        lhs: ir.Math = step.get("lhs") or ir.mtext("")
        rhs: ir.Math | None = step.get("rhs")

        # Private assignment suppression: only when lhs is a simple variable.
        if _is_private_lhs(lhs) and ctx.options.suppress_private_assignments:
            return

        parts: list[ir.Math] = [lhs]
        if rhs is not None:
            parts.append(rhs)
            parts = _maybe_add_substitution(
                ctx, parts, rhs, locals_map, exclude_first=True
            )
        parts = _maybe_add_value(parts, value)
        ctx.append_content(f"<p>{render_equation(parts)}</p>")
        return

    # Fallback: stringify.
    ctx.append_content(f"<p>{html.escape(str(step))}</p>")


def _maybe_add_value(parts: list[ir.Math], value: Any) -> list[ir.Math]:
    if value is None:
        return parts
    value_ir = value_to_ir(value)
    if value_ir not in parts:
        parts.append(value_ir)
    return parts


def _maybe_add_substitution(
    ctx: CalcContext,
    parts: list[ir.Math],
    expr_node: ir.Math,
    locals_map: Mapping[str, Any],
    *,
    exclude_first: bool = False,
) -> list[ir.Math]:
    if not ctx.options.enable_substitution:
        return parts

    substituted = substitute_vars(expr_node, locals_map)
    # Avoid duplication when unchanged.
    if substituted != expr_node:
        parts.append(substituted)
    return parts


def substitute_vars(node: ir.Math, locals_map: Mapping[str, Any]) -> ir.Math:
    """Replace <mi>var</mi> with runtime values when available.

    This is conservative and only substitutes simple variables.
    """

    if node is None:
        return ir.mtext("")

    if isinstance(node, str):
        return node

    if isinstance(node, ir.Mi):
        if node.name in locals_map:
            return value_to_ir(locals_map[node.name])
        return node

    if isinstance(node, ir.MRow):
        return ir.mrow([substitute_vars(ch, locals_map) for ch in node.children])

    if isinstance(node, ir.MFrac):
        return ir.mfrac(
            substitute_vars(node.numerator, locals_map),
            substitute_vars(node.denominator, locals_map),
        )

    if isinstance(node, ir.MSup):
        return ir.msup(
            substitute_vars(node.base, locals_map),
            substitute_vars(node.exponent, locals_map),
        )

    if isinstance(node, ir.MSub):
        return ir.msub(
            substitute_vars(node.base, locals_map),
            substitute_vars(node.subscript, locals_map),
        )

    if isinstance(node, ir.MSqrt):
        return ir.msqrt(substitute_vars(node.body, locals_map))

    if isinstance(node, ir.MFenced):
        return ir.mfenced(
            substitute_vars(node.body, locals_map),
            open=node.open,
            close=node.close,
        )

    # Mn/Mo/MText and unknown nodes remain unchanged.
    return node


def value_to_ir(value: Any) -> ir.MathNode:
    # Numbers
    if isinstance(value, (int, float)):
        return ir.mn(value)

    # Strings
    if isinstance(value, str):
        return ir.mtext(value)

    if isinstance(value, pint.Quantity):
        return ir.mrow([ir.mn(value.magnitude), ir.mo(""), ir.mtext(str(value.units))])

    return ir.mtext(str(value))


def _is_private_lhs(lhs: Any) -> bool:
    return isinstance(lhs, ir.Mi) and lhs.name.startswith("_")
