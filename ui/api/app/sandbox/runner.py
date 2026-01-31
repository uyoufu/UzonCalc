import asyncio
import uuid
import sys
import traceback
import importlib.util
from typing import Any, Callable, Optional, Dict, cast, Awaitable
from dataclasses import asdict

# Adjust import based on workspace structure 'uzoncalc' package availability
from uzoncalc.context import CalcContext
from uzoncalc.interaction import _execution_observer
from uzoncalc.utils.ui import Window
from .models import ExecutionResult, ExecutionStatus


class SandboxRunner:
    def __init__(self, script_path: str, defaults: Optional[Dict[str, Any]] = None):
        """
        :param script_path: 要执行的脚本路径
        :param defaults: 初始参数字典，会注入到 CalcContext.vars 中
        例如: {"title": {"field": value}}
        """
        self.script_path = script_path
        self.defaults = defaults or {}
        self.execution_id = str(uuid.uuid4())

        # Internal state
        self.status = ExecutionStatus.RUNNING
        self.result: Any = None
        self.error: str | None = None
        self.ctx: CalcContext | None = None
        self._task: asyncio.Task | None = None

    def _on_context_created(self, ctx: CalcContext):
        """Callback triggered when the script creates a CalcContext."""
        self.ctx = ctx
        # Inject initial parameters into the context
        if self.defaults:
            ctx.vars.update(self.defaults)

    async def _run_script(self):
        try:
            # 1. Load Module dynamically
            spec = importlib.util.spec_from_file_location(
                f"sandbox_{self.execution_id}", self.script_path
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

            # 3. Request Context Observation
            # This ensures we capture the context created inside the execution
            token = _execution_observer.set(self._on_context_created)

            try:
                # 4. Execute the function
                # is_silent=False enables UI interactions
                func = cast(Callable[..., Awaitable[Any]], entry_point)
                ret_ctx = await func(is_silent=False, defaults=self.defaults)

                # Execution finished successfully
                # Extract results from context (usually vars or logic defined results)
                # Assuming the context object itself is what we care about or its contents
                self.result = ret_ctx.vars if ret_ctx else {}
                self.status = ExecutionStatus.COMPLETED

            finally:
                _execution_observer.reset(token)

        except Exception:
            self.error = traceback.format_exc()
            self.status = ExecutionStatus.FAILED

    def start(self) -> str:
        """Start the execution in a background task."""
        self._task = asyncio.create_task(self._run_script())
        return self.execution_id

    def get_state(self) -> ExecutionResult:
        """Get the current state of execution."""

        # Check task completion status first
        if self._task and self._task.done():
            # If the task is done but status is still RUNNING, implies success or uncaught error handled by async
            if self.status == ExecutionStatus.RUNNING:
                try:
                    self._task.result()
                    self.status = ExecutionStatus.COMPLETED
                except Exception:
                    self.error = traceback.format_exc()
                    self.status = ExecutionStatus.FAILED

        # Check for UI Waiting State
        # If status is RUNNING, check if context is requesting UI
        if self.status == ExecutionStatus.RUNNING and self.ctx:
            interaction = self.ctx.interaction
            if interaction.is_waiting_for_input:
                ui_def = interaction.required_ui

                return ExecutionResult(
                    execution_id=self.execution_id,
                    status=ExecutionStatus.WAITING_FOR_INPUT,
                    ui_definition=asdict(ui_def) if ui_def else None,
                )

        return ExecutionResult(
            execution_id=self.execution_id,
            status=self.status,
            result=self.result,
            error=self.error,
        )

    def submit_input(self, data: Dict[str, Any]):
        """
        Resume execution with provided input.
        :param data: 用户输入数据字典，格式为 {field_name: value}
        """
        current_state = self.get_state()

        if current_state.status != ExecutionStatus.WAITING_FOR_INPUT:
            raise RuntimeError(
                f"Execution is not waiting for input (current: {current_state.status})"
            )

        if self.ctx:
            self.ctx.interaction.set_input(data)
        else:
            raise RuntimeError("Internal error: context not initialized")

    def cancel(self):
        """Cancel the execution."""
        if self._task and not self._task.done():
            self._task.cancel()
            self.status = ExecutionStatus.FAILED
            self.error = "Cancelled by user"
