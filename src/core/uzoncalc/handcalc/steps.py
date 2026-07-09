from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Protocol

from ..context import CalcContext
from . import ir
from .rendering import (
    build_equation_parts,
    build_equation_parts_for_assignment,
    prepare_lhs,
    render_fstring_segments,
    render_html,
    substitute_vars,
    value_to_ir,
)
from .rendering.equation_renderer import is_private_lhs
from .rendering.value_renderer import format_number


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
        render_html(ctx, html.escape(content))


@dataclass(frozen=True, slots=True)
class ExprStep:
    """表达式步骤。"""

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
        parts = build_equation_parts(
            self.expr or ir.mtext(""),
            locals_map or {},
            value,
            enable_formula_expression=ctx.options.enable_formula_expression,
            enable_substitution=ctx.options.enable_substitution,
        )
        if not parts:
            return
        render_html(ctx, ir.equation(parts).to_mathml_xml())


@dataclass(frozen=True, slots=True)
class EquationStep:
    """赋值方程步骤。"""

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
        lhs = prepare_lhs(self.lhs, value, locals_map)

        if is_private_lhs(lhs) and ctx.options.suppress_private_assignments:
            return

        parts = build_equation_parts_for_assignment(
            lhs,
            self.rhs,
            value,
            locals_map,
            enable_formula_expression=ctx.options.enable_formula_expression,
            enable_substitution=ctx.options.enable_substitution,
        )
        if len(parts) <= 1:
            return
        render_html(ctx, ir.equation(parts).to_mathml_xml())


@dataclass(frozen=True, slots=True)
class FStringSegment:
    """f-string 的一个片段。"""

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

    def record(
        self,
        ctx: CalcContext,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> None:
        if ctx.options.skip_content:
            return
        content = render_fstring_segments(self.segments, ctx, locals_map or {})
        render_html(ctx, content)


__all__ = [
    "EquationStep",
    "ExprStep",
    "FStringSegment",
    "FStringStep",
    "Step",
    "TextStep",
    "format_number",
    "substitute_vars",
    "value_to_ir",
]
