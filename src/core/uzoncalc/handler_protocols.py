"""Small structural interfaces shared by document handler pipelines."""

from __future__ import annotations

from typing import Any, Protocol


class HandlerContext(Protocol):
    """Expose only the context options required by output handlers."""

    options: Any


__all__ = ["HandlerContext"]
