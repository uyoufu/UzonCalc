from __future__ import annotations

from typing import Any, Mapping

from core.context import CalcContext
from core.handcalc.steps import Step


def record_step(
    *,
    step: Step,
    locals_map: Mapping[str, Any] | None = None,
    value: Any = None,
) -> None:
    """Record a structured step.

    This is the runtime entry point injected by AST instrumentation.
    The actual behavior lives on the Step subclasses.
    """
    from core.setup import get_current_instance

    ctx = get_current_instance()
    step.record(ctx, locals_map=locals_map, value=value)
