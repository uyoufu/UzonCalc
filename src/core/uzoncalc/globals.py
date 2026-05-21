from contextvars import ContextVar
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .context import CalcContext

_calc_instance = ContextVar[Optional["CalcContext"]]("calc_ctx", default=None)


def get_current_instance() -> "CalcContext":
    inst = _calc_instance.get()
    if inst is None:
        raise RuntimeError("no current instance in this context")
    return inst
