import asyncio
from dataclasses import asdict
import os
from datetime import datetime
from typing import Dict, Any

from .execution_result import ExecutionResult
from .runner import LocalSandboxRunner
from .auto_cleanup import AutoCleanupScheduler

from uzoncalc.utils.ui import UIPayloads


class SandboxManager:
    _instances: Dict[str, LocalSandboxRunner] = {}
    _auto_cleanup = AutoCleanupScheduler()

    @staticmethod
    def generate_result_path(report_id: int) -> str:
        """Generate a unique result path for storing output files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.abspath(
            f"data/public/reports/{report_id}/{timestamp}.html"
        )
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        return output_file

    @classmethod
    async def execute_script(
        cls,
        script_path: str,
        defaults: dict[str, dict[str, Any]] = {},
        is_silent: bool = False,
        package_root: str | None = None,
    ) -> ExecutionResult:
        """
        Start execution of a script.
        Returns the execution_id.
        :param ready_future: 当执行就绪（遇到 UI 或完成）时设置的 Future
        :param package_root: 脚本所在的包根目录路径，会添加到系统路径中
        """
        future: asyncio.Future[UIPayloads] = asyncio.get_running_loop().create_future()

        # 创建新的执行 ID
        runner = LocalSandboxRunner(
            script_path, defaults, is_silent=is_silent, package_root=package_root
        )
        # 启动任务
        runner.start_task(future)
        cls._instances[runner.execution_id] = runner

        try:
            payloads = await future
        except Exception as e:
            SandboxManager.terminate(runner.execution_id)
            raise e

        # 自动清理：
        # - 若已完成，立即清理实例
        # - 若进入交互等待，则按 idle TTL 自动回收
        if not payloads.is_waiting_for_input:
            SandboxManager.terminate(runner.execution_id)
        else:
            cls._auto_cleanup.touch(
                runner.execution_id,
                lambda eid=runner.execution_id: cls.terminate(eid),
            )

        return ExecutionResult(
            executionId=runner.execution_id,
            html=payloads.html,
            isCompleted=not payloads.is_waiting_for_input,
            windows=[asdict(w) for w in payloads.windows] if payloads.windows else [],
        )

    @classmethod
    async def continue_execution(
        cls,
        execution_id: str,
        defaults: dict[str, dict[str, Any]],
    ) -> ExecutionResult:
        """Continue an existing execution with user input."""
        runner = cls._instances.get(execution_id)
        if not runner:
            raise ValueError(f"Execution {execution_id} not found")

        # 创建一个 future
        future: asyncio.Future[UIPayloads] = asyncio.get_running_loop().create_future()
        runner.continue_task(future=future, defaults=defaults)

        try:
            payloads = await future
        except Exception as e:
            SandboxManager.terminate(execution_id)
            raise e

        if not payloads.is_waiting_for_input:
            SandboxManager.terminate(execution_id)
        else:
            cls._auto_cleanup.touch(
                execution_id,
                lambda eid=execution_id: cls.terminate(eid),
            )

        return ExecutionResult(
            executionId=runner.execution_id,
            html=payloads.html,
            isCompleted=not payloads.is_waiting_for_input,
            windows=[asdict(w) for w in payloads.windows] if payloads.windows else [],
        )

    @classmethod
    def terminate(cls, execution_id: str):
        """Force terminate an execution."""
        if execution_id in cls._instances:
            cls._auto_cleanup.cancel(execution_id)
            cls._instances[execution_id].cancel()
            cls._instances.pop(execution_id)
