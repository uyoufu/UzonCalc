from __future__ import annotations

import asyncio
from typing import Callable, Optional

from .errors import SandboxTimeoutError


# 全局超时时长：5 分钟（不对外暴露配置）
_GLOBAL_TIMEOUT_SECONDS = 5 * 60


class GlobalTimeout:
    """全局超时控制：对整个脚本执行过程进行超时控制。
    
    超时参数不对外暴露，固定为 5 分钟。
    """

    def __init__(self):
        self._handle: Optional[asyncio.Handle] = None

    def start(self, on_timeout: Callable[[], None]) -> None:
        """启动全局超时计时器"""
        self.cancel()

        loop = asyncio.get_running_loop()
        self._handle = loop.call_later(_GLOBAL_TIMEOUT_SECONDS, on_timeout)

    def cancel(self) -> None:
        """取消超时计时器"""
        if self._handle is None:
            return
        try:
            self._handle.cancel()
        finally:
            self._handle = None


def build_timeout_error() -> SandboxTimeoutError:
    return SandboxTimeoutError(
        f"Sandbox execution timeout after {_GLOBAL_TIMEOUT_SECONDS} seconds"
    )
