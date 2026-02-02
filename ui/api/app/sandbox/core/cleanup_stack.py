from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, Optional


class CleanupStack:
    """轻量级清理栈：按 LIFO 执行清理回调，支持同步/异步回调。"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._callbacks: list[Callable[[], Any]] = []
        self._closed: bool = False
        self._logger = logger

    def push(self, callback: Callable[[], Any]) -> None:
        if self._closed:
            raise RuntimeError("CleanupStack already closed")
        self._callbacks.append(callback)

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True

        while self._callbacks:
            callback = self._callbacks.pop()
            try:
                result = callback()
                if inspect.isawaitable(result):
                    await result
            except Exception:
                if self._logger:
                    self._logger.exception("Cleanup callback failed")
