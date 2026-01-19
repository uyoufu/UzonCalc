from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ...context import CalcContext


class BasePostHandler:
    """后处理器基类。

    - `priority` 越小越先执行
    - `handle` 支持接收 `ctx`，便于根据 ContextOptions 做处理
    """

    priority: int = 100

    def handle(self, data: str, ctx: Optional[CalcContext] = None) -> str:
        raise NotImplementedError()
