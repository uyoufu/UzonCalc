"""Create the configured singleton execution backend."""

from app.sandbox.core.backend_types import SandboxBackendMode, configured_backend_mode
from app.sandbox.core.executor_bubblewrap import BubblewrapSandboxExecutor
from app.sandbox.core.executor_interface import ISandboxExecutor
from app.sandbox.core.executor_local import InProcessSandboxExecutor
from app.sandbox.core.executor_remote import RemoteDockerSandboxExecutor
from config import app_config

_executor: ISandboxExecutor | None = None


def get_sandbox_executor() -> ISandboxExecutor:
    """Return the singleton matching ``sandbox.mode`` configuration."""
    global _executor
    if _executor is not None:
        return _executor
    mode = configured_backend_mode(app_config.sandbox_mode)
    if mode is SandboxBackendMode.IN_PROCESS:
        _executor = InProcessSandboxExecutor()
    elif mode is SandboxBackendMode.BUBBLEWRAP:
        _executor = BubblewrapSandboxExecutor()
    else:
        _executor = RemoteDockerSandboxExecutor()
    return _executor


async def close_sandbox_executor() -> None:
    """Close and clear the configured singleton backend."""
    global _executor
    if _executor is not None:
        await _executor.close()
        _executor = None
