"""Abstract execution backend shared by all managed sandbox mechanisms."""

from abc import ABC, abstractmethod
from typing import Any

from .backend_types import PreparedExecutionBundle, RuntimeDescriptor
from .execution_result import ExecutionResult


class ISandboxExecutor(ABC):
    """Start, continue, and terminate one bundle-backed execution session."""

    @abstractmethod
    async def runtime_descriptor(self) -> RuntimeDescriptor:
        """Return the exact runtime identity used for build/bundle keys."""

    @abstractmethod
    async def execute_bundle(
        self,
        bundle: PreparedExecutionBundle,
        defaults: dict[str, dict[str, Any]] | None = None,
        is_silent: bool = False,
    ) -> ExecutionResult:
        """Start a new execution from an immutable prepared bundle."""

    @abstractmethod
    async def continue_execution(
        self,
        execution_id: str,
        defaults: dict[str, dict[str, Any]],
    ) -> ExecutionResult:
        """Continue the original session with one user-input payload."""

    @abstractmethod
    async def terminate(self, execution_id: str) -> None:
        """Terminate an active execution and release backend resources."""

    async def close(self) -> None:
        """Close shared backend resources during API shutdown."""
