from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lxml import etree
    from ...context import CalcContext


class BasePostHandler:
    """后处理器基类。

    - `priority` 越小越先执行
    - `handle` 原地修改传入的 lxml 节点
    """

    priority: int = 100

    def handle(self, node: "etree._Element", ctx: "CalcContext | None" = None) -> None:
        raise NotImplementedError()
