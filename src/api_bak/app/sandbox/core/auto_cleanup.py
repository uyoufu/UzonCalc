from __future__ import annotations

import asyncio
from typing import Callable, Optional


_IDLE_TTL_SECONDS = 60 * 10  # 10 minutes


class AutoCleanupScheduler:
    """基于 idle TTL 的自动清理调度器（不对外暴露配置）。"""

    def __init__(self, *, ttl_seconds: int = _IDLE_TTL_SECONDS):
        self._ttl_seconds = ttl_seconds
        self._handles: dict[str, asyncio.Handle] = {}

    def touch(self, execution_id: str, on_expire: Callable[[], None]) -> None:
        """
        触发或重置指定 execution_id 的清理调度
        """

        self.cancel(execution_id)
        loop = asyncio.get_running_loop()
        self._handles[execution_id] = loop.call_later(self._ttl_seconds, on_expire)

    def cancel(self, execution_id: str) -> None:
        handle = self._handles.pop(execution_id, None)
        if handle is None:
            return
        try:
            handle.cancel()
        except Exception:
            pass

    def clear(self) -> None:
        """
        清除所有调度句柄
        """
        for execution_id in list(self._handles.keys()):
            self.cancel(execution_id)
