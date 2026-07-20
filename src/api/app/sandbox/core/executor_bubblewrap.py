"""Linux bubblewrap backend using the shared bundle worker protocol."""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from app.db.models.enums import ExecutorType
from app.service.calc_report_build_service import local_runtime_fingerprint
from config import app_config

from .backend_types import (
    PreparedExecutionBundle,
    RuntimeDescriptor,
    SandboxBackendMode,
)
from .execution_result import ExecutionResult
from .executor_interface import ISandboxExecutor
from .process_session import JsonLineProcessSession, drain_process_stderr


class BubblewrapSandboxExecutor(ISandboxExecutor):
    """Run each bundle worker in a filesystem/network namespace."""

    def __init__(self) -> None:
        """Initialize an empty active-session registry."""
        self._sessions: dict[str, JsonLineProcessSession] = {}

    async def runtime_descriptor(self) -> RuntimeDescriptor:
        """Validate bubblewrap availability and return local toolchain identity."""
        executable = app_config.sandbox_bubblewrap_path
        if not Path(executable).is_file() and shutil.which(executable) is None:
            raise RuntimeError(f"bubblewrap executable not found: {executable}")
        return RuntimeDescriptor(
            mode=SandboxBackendMode.BUBBLEWRAP,
            fingerprint=local_runtime_fingerprint(),
            executor_type=ExecutorType.LOCAL,
            node_id=os.uname().nodename,
        )

    async def execute_bundle(
        self,
        bundle: PreparedExecutionBundle,
        defaults: dict[str, dict[str, Any]] | None = None,
        is_silent: bool = False,
    ) -> ExecutionResult:
        """Start one namespaced worker and retain it only while interactive."""
        command = self._build_command(bundle, is_silent)
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        session = JsonLineProcessSession(
            process=process,
            stderr_task=asyncio.create_task(drain_process_stderr(process.stderr)),
        )
        result = await session.request("start", defaults)
        if result.isCompleted:
            await session.terminate()
        else:
            self._sessions[result.executionId] = session
        return result

    async def continue_execution(
        self,
        execution_id: str,
        defaults: dict[str, dict[str, Any]],
    ) -> ExecutionResult:
        """Continue an active namespaced worker."""
        session = self._sessions.get(execution_id)
        if session is None:
            raise ValueError(f"Execution {execution_id} not found")
        result = await session.request("continue", defaults)
        if result.isCompleted:
            self._sessions.pop(execution_id, None)
            await session.terminate()
        return result

    async def terminate(self, execution_id: str) -> None:
        """Terminate and forget a namespaced worker."""
        session = self._sessions.pop(execution_id, None)
        if session is not None:
            await session.terminate()

    async def close(self) -> None:
        """Terminate all active namespaced workers."""
        sessions = list(self._sessions.values())
        self._sessions.clear()
        await asyncio.gather(*(session.terminate() for session in sessions))

    def _build_command(
        self, bundle: PreparedExecutionBundle, is_silent: bool
    ) -> list[str]:
        """Build a shell-free bubblewrap command with minimum read-only mounts."""
        executable = app_config.sandbox_bubblewrap_path
        command = [
            executable,
            "--die-with-parent",
            "--new-session",
            "--unshare-all",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            "--dir",
            "/work",
            "--ro-bind",
            str(bundle.root),
            "/bundle",
            "--chdir",
            "/work",
        ]
        if app_config.sandbox_network_enabled:
            command.append("--share-net")
        mounted: set[str] = {str(bundle.root)}
        created_parents: set[str] = {"/", "/work", "/bundle"}
        for runtime_path in _runtime_readonly_paths():
            path_text = str(runtime_path)
            if path_text in mounted:
                continue
            for parent in reversed(runtime_path.parents[:-1]):
                parent_text = str(parent)
                if parent_text not in created_parents:
                    command.extend(["--dir", parent_text])
                    created_parents.add(parent_text)
            mounted.add(path_text)
            command.extend(["--ro-bind", path_text, path_text])
        command.extend(
            [
                "--setenv",
                "PYTHONPATH",
                os.pathsep.join(
                    str(path)
                    for path in _runtime_readonly_paths()
                    if path.name in {"api", "core"}
                ),
                sys.executable,
                "-m",
                "app.sandbox.worker",
                "--entry",
                "/bundle/" + bundle.entry_path,
                "--bundle-root",
                "/bundle",
            ]
        )
        if is_silent:
            command.append("--silent")
        return command


def _runtime_readonly_paths() -> list[Path]:
    """Return existing runtime roots needed to import API/core dependencies."""
    candidates = [Path(sys.prefix), Path("/usr"), Path("/lib"), Path("/lib64")]
    for path_text in sys.path:
        if not path_text:
            continue
        path = Path(path_text).resolve()
        if path.is_dir() and path.name in {"api", "core"}:
            candidates.append(path)
    unique: list[Path] = []
    for candidate in candidates:
        if candidate.exists() and candidate not in unique:
            unique.append(candidate)
    return unique
