from __future__ import annotations


class SandboxTimeoutError(TimeoutError):
    """Sandbox 执行超时（内部固定 5 分钟）。"""


class SandboxCancelledError(RuntimeError):
    """Sandbox 执行被取消（例如用户终止或自动清理）。"""
