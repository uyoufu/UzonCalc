import string
from typing import Any, Mapping

from core.context import CalcContext


def record_step(
    ctx: CalcContext,
    *,
    name: str,
    expr: str,
    substitution: Any,
    locals_map: Mapping[str, Any] | None = None,
) -> None:

    def _has_format_fields(fmt: str) -> bool:
        # Detect whether fmt uses any `{field}` placeholders (escaped braces are ignored).
        for _, field_name, _, _ in string.Formatter().parse(fmt):
            if field_name is not None:
                return True
        return False

    locals_map = locals_map or {}
    expr_str = str(expr)
    substitution_str = str(substitution)
    needs_substitution = _has_format_fields(substitution_str)

    if needs_substitution:
        substitution_out = substitution_str.format(**locals_map)
    else:
        substitution_out = substitution_str

    expr_str_out = expr_str.format(**locals_map)
    if needs_substitution:
        substitution_out = substitution_str.format(**locals_map)

        if name:
            ctx.append_content(f"{name} = {expr_str_out} = {substitution_out}")
        else:
            ctx.append_content(f"{expr_str_out} = {substitution_out}")

    else:
        if name:
            ctx.append_content(f"{name} = {expr_str_out}")
        else:
            ctx.append_content(expr_str_out)
