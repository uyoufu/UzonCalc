"""Framed JSON-lines process sessions used by bubblewrap and Docker workers."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from .execution_result import ExecutionResult


@dataclass
class JsonLineProcessSession:
    """Own one worker process and exchange serialized interactive commands."""

    process: asyncio.subprocess.Process
    stderr_task: asyncio.Task | None = None

    async def request(
        self, action: str, defaults: dict[str, dict[str, Any]] | None = None
    ) -> ExecutionResult:
        """Send one action and await one framed execution result.

        Args:
            action: ``start`` or ``continue``.
            defaults: Input/default values for the action.

        Returns:
            Deserialized execution result.

        Raises:
            RuntimeError: If the worker exits, closes the protocol, or returns error.
        """
        if self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("Sandbox worker pipes are unavailable")
        payload = json.dumps(
            {"action": action, "defaults": defaults or {}},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        self.process.stdin.write(payload + b"\n")
        await self.process.stdin.drain()
        response_line = await self.process.stdout.readline()
        if not response_line:
            return_code = await self.process.wait()
            raise RuntimeError(f"Sandbox worker exited with code {return_code}")
        response = json.loads(response_line)
        if not response.get("ok"):
            raise RuntimeError(response.get("error") or "Sandbox worker failed")
        return ExecutionResult.model_validate(response["result"])

    async def terminate(self) -> None:
        """Terminate the worker and drain its stderr task."""
        if self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=3)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
        if self.stderr_task is not None:
            self.stderr_task.cancel()


async def drain_process_stderr(stream: asyncio.StreamReader | None) -> None:
    """Drain worker stderr so verbose user output cannot block the protocol."""
    if stream is None:
        return
    while await stream.readline():
        pass
