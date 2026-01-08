from __future__ import annotations

from typing import Any, Mapping

from core.context import CalcContext
from core.handcalc.v2.record import record_step as record_step_v2
from core.handcalc.v2 import ir


def record_step(
    ctx: CalcContext,
    *,
    step: dict | None = None,
    # legacy args (kept for compatibility with older instrumented code)
    name: str = "",
    expr: str = "",
    substitution: Any = "",
    value: Any = None,
    locals_map: Mapping[str, Any] | None = None,
) -> None:
    """Record a calculation step.

    New mode (preferred): pass `step=...` (structured dict IR).
    Legacy mode: pass name/expr/substitution/value; best-effort conversion.
    """

    if step is not None:
        record_step_v2(ctx, step=step, locals_map=locals_map, value=value)
        return

    # Legacy best-effort: treat inputs as plain text.
    legacy_step = {
        "kind": "equation",
        "lhs": ir.mtext(str(name)) if name else ir.mtext(""),
        "rhs": ir.mtext(str(expr)) if expr else None,
    }
    record_step_v2(ctx, step=legacy_step, locals_map=locals_map, value=value)
