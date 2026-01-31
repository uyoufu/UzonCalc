import asyncio
from dataclasses import asdict
import os
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

from app.sandbox.execution_result import ExecutionResult
from .runner import LocalSandboxRunner
from uzoncalc.utils.ui import UIPayloads


class SandboxManager:
    _instances: Dict[str, LocalSandboxRunner] = {}

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
    ) -> ExecutionResult:
        """
        Start execution of a script.
        Returns the execution_id.
        :param ready_future: 当执行就绪（遇到 UI 或完成）时设置的 Future
        """
        future: asyncio.Future[UIPayloads] = asyncio.get_running_loop().create_future()

        # 创建新的执行 ID
        runner = LocalSandboxRunner(script_path, defaults, is_silent=is_silent)
        # 启动任务
        runner.start_task(future)
        cls._instances[runner.execution_id] = runner

        try:
            payloads = await future
        except Exception as e:
            SandboxManager.terminate(runner.execution_id)
            raise e

        # Cleanup routine could be scheduled here (e.g. remove after 1 hour)
        return ExecutionResult(
            executionId=runner.execution_id,
            window=asdict(payloads.window) if payloads.window else {},
            html=payloads.html,
            isCompleted=payloads.window is None,
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

        return ExecutionResult(
            executionId=runner.execution_id,
            window=asdict(payloads.window) if payloads.window else {},
            html=payloads.html,
            isCompleted=payloads.window is None,
        )

    @classmethod
    def terminate(cls, execution_id: str):
        """Force terminate an execution."""
        if execution_id in cls._instances:
            cls._instances[execution_id].cancel()
            del cls._instances[execution_id]
