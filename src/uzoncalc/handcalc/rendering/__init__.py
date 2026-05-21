"""公式渲染子系统。"""

from .equation_renderer import (
    build_equation_parts,
    build_equation_parts_for_assignment,
    prepare_lhs,
    style_array_vars,
    substitute_vars,
)
from .fstring_renderer import render_fstring_segments
from .html_renderer import render_html
from .value_renderer import (
    FormattedQuantity,
    format_runtime_value,
    format_number,
    is_array_value,
    render_value_fragment,
    render_value_text,
    should_render_runtime_value,
    value_to_ir,
)

__all__ = [
    "build_equation_parts",
    "build_equation_parts_for_assignment",
    "FormattedQuantity",
    "format_runtime_value",
    "format_number",
    "is_array_value",
    "prepare_lhs",
    "render_fstring_segments",
    "render_html",
    "render_value_fragment",
    "render_value_text",
    "should_render_runtime_value",
    "style_array_vars",
    "substitute_vars",
    "value_to_ir",
]
