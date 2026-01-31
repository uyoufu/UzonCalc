import asyncio
import uuid
import sys
import importlib.util
from typing import Any, Callable, Optional, Dict, cast, Awaitable

# Adjust import based on workspace structure 'uzoncalc' package availability
from uzoncalc.context import CalcContext
from uzoncalc.setup import run
from uzoncalc.utils.ui import UIPayloads
from config import logger


class LocalSandboxRunner:
    def __init__(
        self,
        script_path: str,
        defaults: Optional[Dict[str, Any]] = None,
        is_silent: bool = False,
    ):
        """
        :param script_path: 要执行的脚本路径
        :param defaults: 初始参数字典，会注入到 CalcContext.vars 中
        例如: {"title": {"field": value}}
        :param output_dir: HTML 输出目录路径
        :param ready_future: 当执行就绪（遇到 UI 或完成）时设置的 Future
        """
        self.script_path = script_path
        self.defaults = defaults or {}
        self.execution_id = str(uuid.uuid4())
        self.is_silent = is_silent

        self._ctx: Optional[CalcContext] = None
        self._ready_future: Optional[asyncio.Future] = None
        self._task: Optional[asyncio.Task] = None

    def _ctx_hook_created(self, ctx: CalcContext):
        # 注入默认值到 context.vars 中
        self._ctx = ctx
        if self._ready_future:
            self._ctx.interaction.set_result_future(self._ready_future)

    def _set_ready_future(self, future: asyncio.Future):
        self._ready_future = future
        if self._ctx:
            self._ctx.interaction.set_result_future(future)

    async def _run_script(self):
        # 1. Load Module dynamically
        spec = importlib.util.spec_from_file_location(
            f"uzoncalc_{self.execution_id}", self.script_path
        )
        if not spec or not spec.loader:
            raise ImportError(f"Could not load script: {self.script_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        # 2. Find Entry Point (@uzon_calc decorated function)
        entry_point = None
        for name, obj in vars(module).items():
            if callable(obj) and getattr(obj, "_uzon_calc_entry", False):
                entry_point = obj
                break

        if not entry_point:
            raise ValueError(
                "No entry point found. Please decorate a function with @uzon_calc"
            )

        # 4. Execute the function
        # is_silent=False enables UI interactions
        func = cast(Callable[..., Awaitable[Any]], entry_point)

        try:
            ctx = await run(
                func,
                is_silent=self.is_silent,
                defaults=self.defaults,
                ctx_hook_created=self._ctx_hook_created,
            )

            # 调用回调
            if self._ready_future and not self._ready_future.done():
                self._ready_future.set_result(UIPayloads(window=None, html=ctx.html()))
        except Exception as e:
            logger.error(f"Error during script execution: {e}")
            # 设置异常到 future
            if self._ready_future and not self._ready_future.done():
                self._ready_future.set_exception(e)
        finally:
            self.cancel()

    def start_task(self, ready_future: asyncio.Future):
        """
        Start the execution in a background task.
        """

        # 判断是否存在
        if self._task and not self._task.done():
            raise RuntimeError("Execution already started")

        self._set_ready_future(ready_future)
        task = asyncio.create_task(self._run_script())
        self._task = task

    def continue_task(
        self, defaults: dict[str, dict[str, Any]], future: asyncio.Future
    ):
        """
        Continue the execution with user input.
        :param defaults: 用户输入数据
        :param future: 当继续执行完成时设置的 Future
        """

        if not self._task or self._task.done():
            raise RuntimeError("No active execution to continue")

        self._set_ready_future(future)
        # 调用继续逻辑
        if self._ctx:
            self._ctx.interaction.set_inputs(defaults)

    def cancel(self):
        """Cancel the execution."""
        if self._task and not self._task.done():
            self._task.cancel()
            self._ready_future = None
            self.error = "Cancelled by user"
