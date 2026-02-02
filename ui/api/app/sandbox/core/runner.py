import asyncio
import uuid
from typing import Any, Callable, Optional, Dict, cast, Awaitable

# Adjust import based on workspace structure 'uzoncalc' package availability
from uzoncalc.context import CalcContext
from uzoncalc.setup import run
from uzoncalc.utils.ui import UIPayloads
from .dynamic_import import DynamicImportSession
from .errors import SandboxCancelledError
from .timeout_control import GlobalTimeout, build_timeout_error


class LocalSandboxRunner:
    def __init__(
        self,
        script_path: str,
        defaults: Optional[Dict[str, Any]] = None,
        is_silent: bool = False,
        package_root: Optional[str] = None,
    ):
        """
        :param script_path: 要执行的脚本路径
        :param defaults: 初始参数字典，会注入到 CalcContext.vars 中
        例如: {"title": {"field": value}}
        :param output_dir: HTML 输出目录路径
        :param ready_future: 当执行就绪（遇到 UI 或完成）时设置的 Future
        :param package_root: 脚本所在的包根目录路径，会添加到系统路径中
        """
        self.script_path = script_path
        self.defaults = defaults or {}
        self.execution_id = str(uuid.uuid4())
        self.is_silent = is_silent
        self.package_root = package_root

        self._ctx: Optional[CalcContext] = None
        self._ready_future: Optional[asyncio.Future] = None
        self._task: Optional[asyncio.Task] = None

        self.error: Optional[str] = None
        self._timeout = GlobalTimeout()
        self._closed: bool = False

    def _ctx_hook_created(self, ctx: CalcContext):
        # 注入默认值到 context.vars 中
        self._ctx = ctx
        if self._ready_future:
            self._ctx.interaction.set_result_future(self._ready_future)

    def _set_ready_future(self, future: asyncio.Future):
        self._ready_future = future
        if self._ctx:
            self._ctx.interaction.set_result_future(future)

    def _on_global_timeout(self) -> None:
        """全局超时处理：取消整个执行"""
        err = build_timeout_error()
        if self._ready_future and not self._ready_future.done():
            self._ready_future.set_exception(err)
        if self._task and not self._task.done():
            self._task.cancel()

    async def _run_script(self):
        module_name = f"uzoncalc_{self.execution_id}"

        try:
            async with DynamicImportSession(
                module_name=module_name,
                script_path=self.script_path,
                package_root=self.package_root,
            ) as module:
                # 1) 查找入口函数（@uzon_calc 标记）
                entry_point = None
                for _, obj in vars(module).items():
                    if callable(obj) and getattr(obj, "_uzon_calc_entry", False):
                        entry_point = obj
                        break

                if not entry_point:
                    raise ValueError(
                        "No entry point found. Please decorate a function with @uzon_calc"
                    )

                func = cast(Callable[..., Awaitable[Any]], entry_point)

                # 2) 执行脚本（交互模式下，UI 结果会由 ctx.interaction 提前写入 Future）
                ctx = await run(
                    func,
                    is_silent=self.is_silent,
                    defaults=self.defaults,
                    ctx_hook_created=self._ctx_hook_created,
                )

                # 3) 当函数执行结束时，补充一个“完成”结果（如果之前尚未返回 UI）
                if self._ready_future and not self._ready_future.done():
                    # 将收集到的所有 UI windows 一起返回
                    self._ready_future.set_result(
                        UIPayloads(html=ctx.html(), windows=ctx.ui_windows)
                    )

        except asyncio.CancelledError:
            # 取消属于正常控制流（用户终止 / 超时），资源释放交给 finally
            raise
        except Exception as e:
            if self._ready_future and not self._ready_future.done():
                self._ready_future.set_exception(e)
        finally:
            await self._finalize()

    async def _finalize(self) -> None:
        if self._closed:
            return
        self._closed = True

        # 取消全局超时计时器
        self._timeout.cancel()

        # 避免调用方 Future 悬挂
        if self._ready_future and not self._ready_future.done():
            self._ready_future.set_exception(SandboxCancelledError("Cancelled"))

        # 断开引用，便于 GC
        self._ready_future = None
        self._ctx = None

    def start_task(self, ready_future: asyncio.Future):
        """
        Start the execution in a background task.
        """

        # 判断是否存在
        if self._task and not self._task.done():
            raise RuntimeError("Execution already started")

        self._set_ready_future(ready_future)
        # 启动全局超时计时器
        self._timeout.start(self._on_global_timeout)
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
        self.error = "Cancelled"

        if self._ready_future and not self._ready_future.done():
            self._ready_future.set_exception(SandboxCancelledError("Cancelled"))

        if self._task and not self._task.done():
            self._task.cancel()

        # 取消全局超时计时器
        self._timeout.cancel()
