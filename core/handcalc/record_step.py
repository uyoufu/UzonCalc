from __future__ import annotations

from typing import Any, Mapping

from core.context import CalcContext

from core.handcalc.steps import Step


def record_step(
    ctx: CalcContext,
    *,
    step: Step,
    locals_map: Mapping[str, Any] | None = None,
    value: Any = None,
) -> None:
    """Record a structured step.

    The logic lives on the step subclasses; this function is only an entry point
    used by AST instrumentation.
    """

    step.record(ctx, locals_map=locals_map, value=value)
