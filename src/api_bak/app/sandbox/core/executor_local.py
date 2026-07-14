"""
本地 Sandbox 执行器

封装现有的 SandboxManager 逻辑，提供统一的执行器接口
"""

from typing import Any, Dict
from .execution_result import ExecutionResult
from .executor_interface import ISandboxExecutor
from .manager import SandboxManager


class LocalSandboxExecutor(ISandboxExecutor):
    """本地进程内执行器"""

    async def execute_script(
        self,
        script_path: str,
        defaults: Dict[str, Dict[str, Any]] | None = None,
        is_silent: bool = False,
        package_root: str | None = None,
    ) -> ExecutionResult:
        """执行脚本"""
        return await SandboxManager.execute_script(
            script_path=script_path,
            defaults=defaults or {},
            is_silent=is_silent,
            package_root=package_root,
        )

    async def continue_execution(
        self,
        execution_id: str,
        defaults: Dict[str, Dict[str, Any]],
    ) -> ExecutionResult:
        """继续执行"""
        return await SandboxManager.continue_execution(
            execution_id=execution_id,
            defaults=defaults,
        )

    async def terminate(self, execution_id: str) -> None:
        """终止执行"""
        SandboxManager.terminate(execution_id)
