"""Trusted in-process execution backend for configured desktop-style use."""

from typing import Any

from app.db.models.enums import ExecutorType
from app.service.calc_report_build_service import local_runtime_fingerprint

from .backend_types import (
    PreparedExecutionBundle,
    RuntimeDescriptor,
    SandboxBackendMode,
)
from .execution_result import ExecutionResult
from .executor_interface import ISandboxExecutor
from .manager import SandboxManager


class InProcessSandboxExecutor(ISandboxExecutor):
    """Run pre-instrumented bundle code directly inside the API process."""

    async def runtime_descriptor(self) -> RuntimeDescriptor:
        """Return the local Python/toolchain identity."""
        return RuntimeDescriptor(
            mode=SandboxBackendMode.IN_PROCESS,
            fingerprint=local_runtime_fingerprint(),
            executor_type=ExecutorType.LOCAL,
            node_id="api-process",
        )

    async def execute_bundle(
        self,
        bundle: PreparedExecutionBundle,
        defaults: dict[str, dict[str, Any]] | None = None,
        is_silent: bool = False,
    ) -> ExecutionResult:
        """Execute the bundle entry through the existing interactive runner."""
        return await SandboxManager.execute_script(
            script_path=str(bundle.root / bundle.entry_path),
            defaults=defaults or {},
            is_silent=is_silent,
            package_root=str(bundle.root),
        )

    async def continue_execution(
        self,
        execution_id: str,
        defaults: dict[str, dict[str, Any]],
    ) -> ExecutionResult:
        """Continue the matching in-process runner."""
        return await SandboxManager.continue_execution(execution_id, defaults)

    async def terminate(self, execution_id: str) -> None:
        """Cancel and remove the matching in-process runner."""
        SandboxManager.terminate(execution_id)
