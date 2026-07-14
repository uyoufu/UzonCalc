"""
Sandbox 执行器抽象接口

定义统一的执行接口，支持本地进程内调用和远程 HTTP 调用两种方式
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from .execution_result import ExecutionResult


class ISandboxExecutor(ABC):
    """Sandbox 执行器抽象接口"""

    @abstractmethod
    async def execute_script(
        self,
        script_path: str,
        defaults: Dict[str, Dict[str, Any]] | None = None,
        is_silent: bool = False,
        package_root: str | None = None,
    ) -> ExecutionResult:
        """
        启动脚本执行

        :param script_path: 脚本文件路径
        :param defaults: 默认参数字典
        :param is_silent: 是否静默模式
        :param package_root: 脚本所在的包根目录路径，会添加到系统路径中
        :return: 执行结果
        """
        pass

    @abstractmethod
    async def continue_execution(
        self,
        execution_id: str,
        defaults: Dict[str, Dict[str, Any]],
    ) -> ExecutionResult:
        """
        继续执行（提交用户输入）

        :param execution_id: 执行 ID
        :param defaults: 用户输入参数
        :return: 执行结果
        """
        pass

    @abstractmethod
    async def terminate(self, execution_id: str) -> None:
        """
        终止执行

        :param execution_id: 执行 ID
        """
        pass
