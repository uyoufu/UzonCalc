from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...context import CalcContext
    from .dom_utils import PostHandlerNode


class BasePostHandler:
    """后处理器基类。

    - `priority` 越小越先执行
    - `handle` 原地修改传入封装节点
    """

    priority: int = 100

    def handle(
        self, post_node: "PostHandlerNode", ctx: "CalcContext | None" = None
    ) -> None:
        raise NotImplementedError()
