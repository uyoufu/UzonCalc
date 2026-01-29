"""
沙箱执行器

核心执行引擎，整合模块加载和生成器管理。
负责将 UzonCalc 函数转换为异步生成器并执行。
"""

import logging
from typing import Optional, Any

from .module_loader import SandboxModuleLoader
from .generator_manager import GeneratorManager, ExecutionStatus

logger = logging.getLogger(__name__)


class CalcSandboxExecutor:
    """
    沙箱中的计算执行器

    职责：
    1. 加载用户定义的计算函数
    2. 将函数转换为异步生成器
    3. 管理多个并发的计算会话
    4. 处理 UI 中断和恢复
    """

    def __init__(
        self,
        safe_dirs: Optional[list[str]] = None,
        session_timeout: int = 3600,
    ):
        """
        Args:
            safe_dirs: 允许加载的目录白名单
            session_timeout: 会话超时时间（秒）
        """
        self.loader = SandboxModuleLoader(safe_dirs=safe_dirs)
        self.generator_manager = GeneratorManager()
        self.session_timeout = session_timeout

    async def initialize(self):
        """初始化执行器"""
        await self.generator_manager.start()
        logger.info("CalcSandboxExecutor initialized")

    async def shutdown(self):
        """关闭执行器"""
        await self.generator_manager.stop()
        logger.info("CalcSandboxExecutor shutdown")

    async def execute_function(
        self,
        file_path: str,
        func_name: str,
        session_id: str,
        params: dict[str, Any],
    ) -> tuple[ExecutionStatus, Optional[dict], str]:
        """
        执行计算函数的第一步

        Args:
            file_path: 函数所在的 .py 文件路径
            func_name: 函数名称
            session_id: 会话 ID（用于跟踪）
            params: 传递给函数的参数

        Returns:
            (status, current_ui_or_none, accumulated_html)

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 函数不存在或路径不安全
            Exception: 执行过程中的其他错误
        """
        try:
            # 加载函数
            func = self.loader.load_function(file_path, func_name)

            # 调用函数获得生成器
            # 函数应该是一个被 @uzon_calc 装饰的异步函数
            # 或者返回异步生成器
            gen = func(**params)

            # 确保是生成器
            if not hasattr(gen, "__anext__"):
                raise ValueError(
                    f"Function '{func_name}' did not return an async generator"
                )

            # 启动会话
            status, ui, html = await self.generator_manager.start_session(
                session_id, gen
            )

            logger.info(
                f"Started execution: session_id={session_id}, file={file_path}, "
                f"func={func_name}, status={status.value}"
            )

            return (status, ui, html)

        except Exception as e:
            logger.error(
                f"Error executing function {func_name}: {e}",
                exc_info=True,
            )
            raise

    async def resume_execution(
        self,
        session_id: str,
        user_input: dict[str, Any],
    ) -> tuple[ExecutionStatus, Optional[dict], str]:
        """
        从 UI 中断点继续执行

        Args:
            session_id: 会话 ID
            user_input: 用户在 UI 中的输入（表单数据）

        Returns:
            (status, current_ui_or_none, accumulated_html)

        Raises:
            ValueError: 会话不存在或状态不对
            Exception: 执行过程中的其他错误
        """
        try:
            status, ui, html = await self.generator_manager.resume_session(
                session_id, user_input
            )

            logger.info(
                f"Resumed execution: session_id={session_id}, "
                f"status={status.value}, ui_found={ui is not None}"
            )

            return (status, ui, html)

        except Exception as e:
            logger.error(
                f"Error resuming execution {session_id}: {e}",
                exc_info=True,
            )
            raise

    def cancel_execution(self, session_id: str):
        """取消执行"""
        self.generator_manager.cancel_session(session_id)
        logger.info(f"Cancelled execution: {session_id}")

    def get_session_status(self, session_id: str) -> Optional[dict]:
        """获取会话状态"""
        return self.generator_manager.get_session_info(session_id)

    def get_all_sessions(self) -> list[dict]:
        """获取所有活跃会话"""
        return self.generator_manager.get_all_sessions()

    def get_cache_info(self) -> dict:
        """获取模块加载缓存信息"""
        return self.loader.get_cache_info()

    def invalidate_module_cache(self, file_path: str):
        """
        使模块缓存失效
        用于文件更新后强制重新加载
        """
        self.loader.invalidate_cache(file_path)
        logger.info(f"Invalidated cache for: {file_path}")

    def clear_all_cache(self):
        """清除所有缓存"""
        self.loader.clear_cache()
        logger.info("Cleared all module cache")


# 全局执行器实例
_executor: Optional[CalcSandboxExecutor] = None


def get_executor() -> CalcSandboxExecutor:
    """获取全局执行器实例"""
    global _executor
    if _executor is None:
        _executor = CalcSandboxExecutor()
    return _executor


def set_executor(executor: CalcSandboxExecutor):
    """设置全局执行器实例"""
    global _executor
    _executor = executor
