from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

import pint

from core.context import CalcContext
from core.handcalc import ir
from core.handcalc.transformers import transform_ir


class StepType:
    """步骤类型常量"""

    TEXT = "text"
    EQUATION = "equation"
    FSTRING = "fstring"


class StepDataKey:
    """步骤数据字典的键名常量"""

    TYPE = "type"
    CONTENT = "content"
    PARTS = "parts"
    LHS = "lhs"
    SEGMENTS = "segments"
    LOCALS = "locals"


class Step(Protocol):
    def record(
        self,
        ctx: CalcContext,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> None: ...

    def to_data(
        self,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> dict[str, Any]:
        """将步骤转换为数据字典，供渲染器使用"""
        ...


@dataclass(frozen=True, slots=True)
class TextStep:
    """Render a text paragraph.

    If `value` is provided at runtime, it wins (used by f-strings).
    """

    text: str = ""

    def to_data(
        self,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> dict[str, Any]:
        """返回文本步骤的数据表示"""
        output = value if value is not None else self.text
        return {
            StepDataKey.TYPE: StepType.TEXT,
            StepDataKey.CONTENT: str(output),
        }

    def record(
        self,
        ctx: CalcContext,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> None:
        if ctx.options.skip_content:
            return

        data = self.to_data(locals_map=locals_map, value=value)
        # 在 inline 模式下使用 span 标签，否则使用 p 标签
        if ctx.is_inline_mode:
            ctx.append_content(f"<span>{html.escape(data[StepDataKey.CONTENT])}</span>")
        else:
            ctx.append_content(f"<p>{html.escape(data[StepDataKey.CONTENT])}</p>")


@dataclass(frozen=True, slots=True)
class ExprStep:
    expr: ir.MathNode

    def to_data(
        self,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> dict[str, Any]:
        """返回表达式步骤的数据表示"""
        locals_map = locals_map or {}
        expr_node: ir.MathNode = self.expr or ir.mtext("")
        parts: list[ir.MathNode] = [expr_node]
        parts = _maybe_add_substitution_data(parts, expr_node, locals_map)
        parts = _maybe_add_value_data(parts, value)
        return {
            StepDataKey.TYPE: StepType.EQUATION,
            StepDataKey.PARTS: parts,
        }

    def record(
        self,
        ctx: CalcContext,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> None:
        if ctx.options.skip_content:
            return

        data = self.to_data(locals_map=locals_map, value=value)
        # 在 inline 模式下使用 span 标签，否则使用 p 标签
        if ctx.is_inline_mode:
            ctx.append_content(
                f"<span>{ir.equation(data[StepDataKey.PARTS]).to_mathml_xml()}</span>"
            )
        else:
            ctx.append_content(
                f"<p>{ir.equation(data[StepDataKey.PARTS]).to_mathml_xml()}</p>"
            )


@dataclass(frozen=True, slots=True)
class EquationStep:
    lhs: ir.MathNode
    rhs: ir.MathNode | None

    def to_data(
        self,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> dict[str, Any]:
        """返回方程步骤的数据表示"""
        lhs: ir.MathNode = self.lhs or ir.mtext("")
        rhs = self.rhs
        locals_map = locals_map or {}

        parts: list[ir.MathNode] = [lhs]
        if rhs is not None:
            parts.append(rhs)
            parts = _maybe_add_substitution_data(parts, rhs, locals_map)

        parts = _maybe_add_value_data(parts, value)
        return {
            StepDataKey.TYPE: StepType.EQUATION,
            StepDataKey.PARTS: parts,
            StepDataKey.LHS: lhs,
        }

    def record(
        self,
        ctx: CalcContext,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> None:
        if ctx.options.skip_content:
            return

        data = self.to_data(locals_map=locals_map, value=value)
        lhs = data[StepDataKey.LHS]

        # Private assignment suppression: only when lhs is a simple variable.
        if _is_private_lhs(lhs) and ctx.options.suppress_private_assignments:
            return

        # 在 inline 模式下使用 span 标签，否则使用 p 标签
        if ctx.is_inline_mode:
            ctx.append_content(
                f"<span>{ir.equation(data[StepDataKey.PARTS]).to_mathml_xml()}</span>"
            )
        else:
            ctx.append_content(
                f"<p>{ir.equation(data[StepDataKey.PARTS]).to_mathml_xml()}</p>"
            )


def _maybe_add_value_data(parts: list[ir.MathNode], value: Any) -> list[ir.MathNode]:
    """内部辅助函数：为数据添加值节点"""
    if value is None:
        return parts
    value_ir = value_to_ir(value)
    if value_ir not in parts:
        parts.append(value_ir)
    return parts


def _maybe_add_substitution_data(
    parts: list[ir.MathNode],
    expr_node: ir.MathNode,
    locals_map: Mapping[str, Any],
) -> list[ir.MathNode]:
    """内部辅助函数：为数据添加替换节点"""
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


@dataclass(frozen=True, slots=True)
class FStringStep:
    """Render an f-string as mixed text + inline equations.

    segments is a list containing either:
    - str: literal text
    - dict: formatted expression descriptor
        - {"kind": "expr", "expr": MathNode}
        - {"kind": "namedexpr", "lhs": MathNode, "rhs": MathNode}

    Note: We intentionally do NOT rely on the runtime evaluated f-string `value`
    because doing so would re-evaluate expressions (side effects, walrus, etc.).
    """

    segments: list[Any]

    def _render_math(
        self,
        expr_desc: Mapping[str, Any],
        locals_map: Mapping[str, Any],
    ) -> str:
        kind = expr_desc.get("kind")
        value_var = expr_desc.get("value_var", "")

        if kind == "namedexpr":
            lhs = expr_desc.get("lhs") or ir.mtext("")
            rhs = expr_desc.get("rhs") or ir.mtext("")
            parts: list[ir.MathNode] = [lhs, rhs]
            parts = _maybe_add_substitution_data(parts, rhs, locals_map)
            # Append final value from runtime.
            if value_var and value_var in locals_map:
                parts = _maybe_add_value_data(parts, locals_map[value_var])
            return ir.equation(parts).to_mathml_xml()

        # Default: treat as a normal expression.
        expr_node = expr_desc.get("expr") or ir.mtext("")
        parts = [expr_node]
        parts = _maybe_add_substitution_data(parts, expr_node, locals_map)
        # Append final value from runtime.
        if value_var and value_var in locals_map:
            parts = _maybe_add_value_data(parts, locals_map[value_var])
        return ir.equation(parts).to_mathml_xml()

    def to_data(
        self,
        *,
        locals_map: Mapping[str, Any] | None = None,
        value: Any = None,
    ) -> dict[str, Any]:
        locals_map = locals_map or {}
        return {
            StepDataKey.TYPE: StepType.FSTRING,
            StepDataKey.SEGMENTS: list(self.segments),
            StepDataKey.LOCALS: dict(locals_map),
        }

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
        out_parts: list[str] = []
        for seg in self.segments:
            if isinstance(seg, str):
                out_parts.append(html.escape(seg))
                continue

            if isinstance(seg, Mapping):
                out_parts.append(self._render_math(seg, locals_map))
                continue

            # Fallback: stringify.
            out_parts.append(html.escape(str(seg)))

        content = "".join(out_parts)
        if ctx.is_inline_mode:
            ctx.append_content(f"<span>{content}</span>")
        else:
            ctx.append_content(f"<p>{content}</p>")
