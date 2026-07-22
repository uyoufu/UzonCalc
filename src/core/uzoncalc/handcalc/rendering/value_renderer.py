from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any

import pint

from ...globals import get_current_instance
from ...context_utils.element_models import HtmlFragment
from .. import ir
from .value_normalizer import normalize_renderable_value

FLOAT_PRECISION = 12  # 浮点数清理精度（消除浮点误差）
SYMBOL_COMMA = ","
SYMBOL_LEFT_BRACKET = "["
SYMBOL_RIGHT_BRACKET = "]"


@dataclass(frozen=True, slots=True)
class FormattedQuantity:
    """A quantity whose magnitude has already been formatted for display."""

    magnitude: str
    units: str


def should_render_runtime_value(value: Any) -> bool:
    """仅展示稳定、可读的运行期值，避免复杂对象 repr 污染计算书。"""
    if isinstance(value, FormattedQuantity):
        return True
    return normalize_renderable_value(value) is not None


def is_array_value(value: Any) -> bool:
    """判断运行期值是否应按数组样式展示。"""
    normalized_value = normalize_renderable_value(value)
    return isinstance(normalized_value, list)


def value_to_ir(value: Any) -> ir.MathNode:
    """将 Python 运行期值转换为 MathIR。"""
    normalized_value = normalize_renderable_value(value)
    if normalized_value is None and not isinstance(value, FormattedQuantity):
        return ir.mtext("")
    value = normalized_value if normalized_value is not None else value

    if isinstance(value, ir.MathNode):
        return value

    if isinstance(value, FormattedQuantity):
        return _quantity_to_ir(value.magnitude, value.units)

    # Numbers
    if isinstance(value, (int, float)):
        return ir.mn(format_number(value))

    # Strings
    if isinstance(value, str):
        return ir.mtext(value)

    if isinstance(value, list):
        return _array_to_ir(value)

    if isinstance(value, pint.Quantity):
        # 使用 format_number 处理浮点数精度问题
        magnitude = value.magnitude
        normalized_magnitude = normalize_renderable_value(magnitude)
        formatted_magnitude = (
            format_number(normalized_magnitude)
            if isinstance(normalized_magnitude, (int, float))
            else str(magnitude)
        )
        return _quantity_to_ir(formatted_magnitude, str(value.units))

    return ir.mtext(str(value))


def render_value_text(value: Any) -> str:
    """Render a runtime value as escaped text without MathML wrappers."""
    if value is None:
        return ""

    if isinstance(value, ir.MathNode):
        return _math_node_to_text(value)
    if isinstance(value, FormattedQuantity):
        return f"{value.magnitude} {value.units}"
    normalized_value = normalize_renderable_value(value)
    if normalized_value is not None:
        value = normalized_value
    if isinstance(value, str):
        return value

    if isinstance(value, (int, float)):
        return format_number(value)

    if isinstance(value, pint.Quantity):
        magnitude = value.magnitude
        formatted = (
            format_number(magnitude)
            if isinstance(magnitude, (int, float))
            else str(magnitude)
        )
        return f"{formatted} {value.units}"

    return str(value)


def render_value_fragment(value: Any) -> str:
    """Render a runtime value for f-string mixed HTML output."""
    if value is None:
        return ""
    html_fragment = render_html_fragment(value)
    if html_fragment is not None:
        return html_fragment
    if isinstance(value, ir.MathNode):
        return value.to_mathml_xml()
    if should_render_runtime_value(value):
        return value_to_ir(value).to_mathml_xml()
    return render_value_text(value)


def render_html_fragment(value: Any) -> str | None:
    """若值是可信 HTML 片段则返回原始 HTML，否则返回 None。"""
    if isinstance(value, HtmlFragment):
        return value.__html__()
    html_method = getattr(value, "__html__", None)
    if callable(html_method):
        return str(html_method())
    return None


def format_runtime_value(value: Any, format_spec: str) -> Any:
    """Apply an f-string format spec without choosing the final output format."""
    if not format_spec or value is None:
        return value

    if isinstance(value, pint.Quantity):
        # 分别格式化数值和单位
        formatted_magnitude = format(value.magnitude, format_spec)
        return FormattedQuantity(formatted_magnitude, str(value.units))

    # 对于非 Quantity 值，直接格式化
    return format(value, format_spec)


def apply_format_spec(value: Any, format_spec: str) -> Any:
    """Backward-compatible alias for f-string runtime formatting."""
    return format_runtime_value(value, format_spec)


def _quantity_to_ir(magnitude: str, units: str) -> ir.MathNode:
    return ir.mrow([ir.mn(magnitude), ir.mo(""), ir.mu(units)])


def _array_to_ir(value: list[Any] | tuple[Any, ...]) -> ir.MathNode:
    """Render a Python sequence as a one-dimensional array or matrix."""
    if _is_rectangular_two_dimensional_array(value):
        return _matrix_array_to_ir(value)

    items: list[ir.MathNode] = []
    for idx, item in enumerate(value):
        if idx:
            items.append(ir.mo(SYMBOL_COMMA))
        items.append(value_to_ir(item))
    return ir.mrow_array(
        [ir.mo(SYMBOL_LEFT_BRACKET), *items, ir.mo(SYMBOL_RIGHT_BRACKET)]
    )


def _is_rectangular_two_dimensional_array(value: list[Any] | tuple[Any, ...]) -> bool:
    """Return True when a sequence can be displayed as a rectangular matrix."""
    if not value:
        return False
    if not all(_is_runtime_sequence(row) for row in value):
        return False

    first_row_length = len(value[0])
    for row in value:
        if len(row) != first_row_length:
            return False
        if any(_is_runtime_sequence(cell) for cell in row):
            return False
    return True


def _matrix_array_to_ir(value: list[Any] | tuple[Any, ...]) -> ir.MathNode:
    """Render a rectangular two-dimensional sequence with MathML table rows."""
    rows = [ir.mtr([ir.mtd([value_to_ir(cell)]) for cell in row]) for row in value]
    return ir.mrow_array(
        [ir.mo(SYMBOL_LEFT_BRACKET), ir.mtable(rows), ir.mo(SYMBOL_RIGHT_BRACKET)]
    )


def _is_runtime_sequence(value: Any) -> bool:
    """Return True for runtime sequence containers that represent arrays."""
    return isinstance(value, (list, tuple))


def _math_node_to_text(value: ir.MathNode) -> str:
    if isinstance(value, ir.MText):
        return value.text
    if isinstance(value, ir.Mn):
        return value.value
    if isinstance(value, ir.Mi):
        return value.name
    if isinstance(value, ir.Mo):
        return value.symbol
    if isinstance(value, ir.Mu):
        return value.name
    if isinstance(value, ir.MRow):
        return "".join(_math_node_to_text(child) for child in value.children)
    return value.to_mathml_xml()


def clean_float(value: float, precision: int = FLOAT_PRECISION) -> float:
    """清理浮点数精度问题。"""
    # 使用 round 移除浮点数运算误差
    return round(value, precision)


def get_float_precision() -> int:
    """获取当前上下文的小数显示精度。"""
    ctx = get_current_instance()
    return max(0, ctx.options.float_precision)


def format_number(value: float | int, float_precision: int | None = None) -> str:
    """按当前上下文精度格式化数字，并移除多余尾零。"""
    if isinstance(value, int):
        return str(value)

    # 未显式传入精度时，沿用当前计算上下文配置。
    display_precision = (
        get_float_precision() if float_precision is None else max(0, float_precision)
    )

    # 先做一次足够精细的浮点清理，再按当前显示精度四舍五入
    cleaned = clean_float(value, max(display_precision, FLOAT_PRECISION))

    # 如果是整数值，不显示小数部分
    if cleaned == int(cleaned):
        return str(int(cleaned))

    formatted = f"{cleaned:.{display_precision}f}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted or "0"
