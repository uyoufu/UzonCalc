import string
from typing import Any, Mapping

from core.context import CalcContext


def record_step(
    ctx: CalcContext,
    *,
    name: str,
    expr: str,
    substitution: Any,
    value: Any = None,
    locals_map: Mapping[str, Any] | None = None,
) -> None:
    # 如果跳过内容记录，直接返回
    if ctx.options.skip_content:
        return

    locals_map = locals_map or {}
    expr_str = str(expr)
    substitution_str = str(substitution)
    # needs_substitution = _has_format_fields(substitution_str)
    needs_substitution = True

    if needs_substitution:
        substitution_out = substitution_str.format(**locals_map)
    else:
        substitution_out = substitution_str

    expr_str_out = expr_str.format(**locals_map)

    value_part = str(value) if value is not None else ""

    parts = [name if name else "", expr_str_out]

    if needs_substitution and substitution_out not in parts:
        parts.append(substitution_out)

    # 添加 value 部分
    if value_part not in parts:
        parts.append(str(value_part))

    # 过滤空部分
    parts = [f"<mrow>{part}</mrow>" for part in parts if part]
    if parts:
        ctx.append_content(
            f"<p><math xmlns='http://www.w3.org/1998/Math/MathML'><mrow>{"<mo>=</mo>".join(parts)}</mrow></math></p>"
        )
