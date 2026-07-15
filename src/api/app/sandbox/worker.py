"""Bundle worker implementing the shared JSON-lines interactive protocol."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.sandbox.core.manager import SandboxManager


def _parse_args() -> argparse.Namespace:
    """Parse the immutable bundle entry arguments supplied by a backend."""
    parser = argparse.ArgumentParser(description="Run one UzonCalc bundle session")
    parser.add_argument("--entry", required=True)
    parser.add_argument("--bundle-root", required=True)
    parser.add_argument("--silent", action="store_true")
    return parser.parse_args()


async def run_worker() -> int:
    """Read framed commands, execute one session, and write framed results."""
    args = _parse_args()
    protocol_output = sys.stdout
    sys.stdout = sys.stderr
    execution_id = None
    while True:
        line = await asyncio.to_thread(sys.stdin.readline)
        if not line:
            if execution_id:
                SandboxManager.terminate(execution_id)
            return 0
        try:
            request = json.loads(line)
            if request.get("action") == "start":
                result = await SandboxManager.execute_script(
                    script_path=args.entry,
                    defaults=request.get("defaults") or {},
                    is_silent=args.silent,
                    package_root=args.bundle_root,
                )
                execution_id = result.executionId
            elif request.get("action") == "continue" and execution_id:
                result = await SandboxManager.continue_execution(
                    execution_id, request.get("defaults") or {}
                )
            else:
                raise ValueError("Invalid worker action or missing active session")
            response = {"ok": True, "result": result.model_dump()}
            protocol_output.write(json.dumps(response, ensure_ascii=False) + "\n")
            protocol_output.flush()
            if result.isCompleted:
                return 0
        except Exception as error:
            protocol_output.write(
                json.dumps(
                    {"ok": False, "error": f"{type(error).__name__}: {error}"},
                    ensure_ascii=False,
                )
                + "\n"
            )
            protocol_output.flush()
            return 1


def main() -> None:
    """Run the worker CLI and exit with its protocol status."""
    raise SystemExit(asyncio.run(run_worker()))


if __name__ == "__main__":
    main()
