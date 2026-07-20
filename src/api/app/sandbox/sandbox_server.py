"""Authenticated artifact-caching Docker sandbox service."""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import os
import shutil
import socket
import stat
import tempfile
import uuid
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path, PurePosixPath
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.sandbox.core.execution_result import ExecutionResult
from app.sandbox.core.process_session import (
    JsonLineProcessSession,
    drain_process_stderr,
)
from config import app_config

_CACHE_ROOT = Path(os.getenv("UZONCALC_SANDBOX_CACHE", "data/sandbox-cache"))
_ARTIFACT_ROOT = _CACHE_ROOT / "artifacts" / "sha256"
_BUNDLE_ROOT = _CACHE_ROOT / "bundles" / "sha256"
_EXECUTION_ROOT = _CACHE_ROOT / "executions"


class BundlePrepareRequest(BaseModel):
    """Describe one immutable bundle requested by the main API."""

    bundleHash: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest: dict


class BundlePrepareResponse(BaseModel):
    """Return missing artifacts and whether bundle assembly is ready."""

    missingArtifacts: list[str]
    isReady: bool


class DockerExecuteRequest(BaseModel):
    """Start one Docker execution from a prepared bundle."""

    bundleHash: str = Field(pattern=r"^[0-9a-f]{64}$")
    entryPath: str
    defaults: dict[str, dict[str, Any]] = Field(default_factory=dict)
    isSilent: bool = False


class ContinueExecutionRequest(BaseModel):
    """Continue one active Docker worker."""

    executionId: str
    defaults: dict[str, dict[str, Any]] = Field(default_factory=dict)


class TerminateExecutionRequest(BaseModel):
    """Terminate one active Docker worker."""

    executionId: str


class DockerSession:
    """Own one docker-run process, container name, and framed worker session."""

    def __init__(
        self,
        container_name: str,
        protocol: JsonLineProcessSession,
        execution_dir: Path,
    ) -> None:
        """Initialize session resources after a successful container launch."""
        self.container_name = container_name
        self.protocol = protocol
        self.execution_dir = execution_dir

    async def terminate(self) -> None:
        """Stop the worker, force-remove its container, and delete scratch data."""
        await self.protocol.terminate()
        process = await asyncio.create_subprocess_exec(
            "docker",
            "rm",
            "-f",
            self.container_name,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.wait()
        shutil.rmtree(self.execution_dir, ignore_errors=True)


class DockerSessionManager:
    """Start and route interactive workers in hardened Docker containers."""

    def __init__(self) -> None:
        """Initialize active sessions and unresolved runtime capabilities."""
        self.sessions: dict[str, DockerSession] = {}
        self.runtime_image_digest: str | None = None

    async def initialize(self) -> None:
        """Resolve the configured runtime image to its immutable digest."""
        configured_digest = app_config.sandbox_runtime_image_digest
        if configured_digest:
            self.runtime_image_digest = configured_digest
            return
        process = await asyncio.create_subprocess_exec(
            "docker",
            "image",
            "inspect",
            "--format",
            "{{.Id}}",
            app_config.sandbox_runtime_image,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(
                f"Unable to inspect sandbox image: {stderr.decode().strip()}"
            )
        self.runtime_image_digest = stdout.decode().strip()

    async def start(self, request: DockerExecuteRequest) -> ExecutionResult:
        """Start one hardened container and return its first interaction result."""
        bundle_root = _bundle_path(request.bundleHash)
        if not (bundle_root / "manifest.json").is_file():
            raise ValueError("Execution bundle is not prepared")
        execution_dir = _EXECUTION_ROOT / uuid.uuid4().hex
        work_dir = execution_dir / "work"
        output_dir = execution_dir / "output"
        work_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        container_name = f"uzoncalc-exec-{uuid.uuid4().hex[:16]}"
        command = self._docker_command(
            container_name,
            bundle_root,
            work_dir,
            output_dir,
            request.entryPath,
            request.isSilent,
        )
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        protocol = JsonLineProcessSession(
            process=process,
            stderr_task=asyncio.create_task(drain_process_stderr(process.stderr)),
        )
        session = DockerSession(container_name, protocol, execution_dir)
        try:
            result = await protocol.request("start", request.defaults)
        except Exception:
            await session.terminate()
            raise
        if result.isCompleted:
            await session.terminate()
        else:
            self.sessions[result.executionId] = session
        return result

    async def continue_session(
        self, execution_id: str, defaults: dict[str, dict[str, Any]]
    ) -> ExecutionResult:
        """Continue the exact container holding an interactive Python session."""
        session = self.sessions.get(execution_id)
        if session is None:
            raise KeyError(execution_id)
        result = await session.protocol.request("continue", defaults)
        if result.isCompleted:
            self.sessions.pop(execution_id, None)
            await session.terminate()
        return result

    async def terminate_session(self, execution_id: str) -> None:
        """Terminate one active Docker session if present."""
        session = self.sessions.pop(execution_id, None)
        if session is not None:
            await session.terminate()

    async def close(self) -> None:
        """Terminate every active container during service shutdown."""
        sessions = list(self.sessions.values())
        self.sessions.clear()
        await asyncio.gather(*(session.terminate() for session in sessions))

    def _docker_command(
        self,
        container_name: str,
        bundle_root: Path,
        work_dir: Path,
        output_dir: Path,
        entry_path: str,
        is_silent: bool,
    ) -> list[str]:
        """Build a shell-free Docker command with explicit isolation limits."""
        command = [
            "docker",
            "run",
            "--rm",
            "-i",
            "--name",
            container_name,
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            str(app_config.sandbox_pids_limit),
            "--memory",
            str(app_config.sandbox_memory_limit),
            "--cpus",
            str(app_config.sandbox_cpu_limit),
            "--network",
            "bridge" if app_config.sandbox_network_enabled else "none",
            "--mount",
            f"type=bind,src={bundle_root},dst=/bundle,readonly",
            "--mount",
            f"type=bind,src={work_dir},dst=/work",
            "--mount",
            f"type=bind,src={output_dir},dst=/output",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--workdir",
            "/work",
            app_config.sandbox_runtime_image,
            "python",
            "-m",
            "app.sandbox.worker",
            "--entry",
            "/bundle/" + _safe_relative_path(entry_path),
            "--bundle-root",
            "/bundle",
        ]
        if is_silent:
            command.append("--silent")
        return command


manager = DockerSessionManager()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize Docker capabilities and clean sessions on shutdown."""
    _ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    _BUNDLE_ROOT.mkdir(parents=True, exist_ok=True)
    _EXECUTION_ROOT.mkdir(parents=True, exist_ok=True)
    await manager.initialize()
    yield
    await manager.close()


app = FastAPI(title="UzonCalc Docker Sandbox", lifespan=lifespan)


def authenticate_service(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Require the configured internal bearer token on every sandbox endpoint."""
    expected = f"Bearer {app_config.sandbox_remote_token}"
    if authorization != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@app.get("/sandbox/health", dependencies=[Depends(authenticate_service)])
async def health_check() -> dict:
    """Return Docker node and exact runtime compatibility information."""
    return {
        "status": "healthy",
        "nodeId": socket.gethostname(),
        "runtimeImageDigest": manager.runtime_image_digest,
        "runtimeFingerprint": (
            f"docker:{manager.runtime_image_digest}:instrumentation-1"
        ),
    }


@app.post(
    "/sandbox/bundles/prepare",
    response_model=BundlePrepareResponse,
    dependencies=[Depends(authenticate_service)],
)
async def prepare_bundle(request: BundlePrepareRequest) -> BundlePrepareResponse:
    """Report artifact misses or atomically assemble a complete cached bundle."""
    canonical = json.dumps(
        request.manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != request.bundleHash:
        raise HTTPException(status_code=400, detail="Bundle hash mismatch")
    artifact_hashes = {
        component[key]
        for component in request.manifest.get("components", [])
        for key in ("sourceArtifactHash", "executionArtifactHash")
    }
    missing = sorted(
        content_hash
        for content_hash in artifact_hashes
        if not (_artifact_path(content_hash) / "manifest.json").is_file()
    )
    if not missing:
        _assemble_remote_bundle(request.bundleHash, request.manifest)
    return BundlePrepareResponse(missingArtifacts=missing, isReady=not missing)


@app.put(
    "/sandbox/artifacts/{content_hash}",
    dependencies=[Depends(authenticate_service)],
)
async def upload_artifact(
    content_hash: str,
    manifest: Annotated[UploadFile, File()],
    payload: Annotated[UploadFile, File()],
) -> dict:
    """Validate and atomically publish one uploaded immutable artifact."""
    if len(content_hash) != 64 or any(
        char not in "0123456789abcdef" for char in content_hash
    ):
        raise HTTPException(status_code=400, detail="Invalid artifact hash")
    manifest_bytes = await manifest.read(app_config.calc_report_max_total_size)
    payload_bytes = await payload.read(app_config.calc_report_max_total_size + 1)
    if len(payload_bytes) > app_config.calc_report_max_total_size:
        raise HTTPException(status_code=413, detail="Artifact payload is too large")
    try:
        manifest_value = json.loads(manifest_bytes)
        canonical = json.dumps(
            manifest_value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if hashlib.sha256(canonical).hexdigest() != content_hash:
            raise ValueError("Artifact hash mismatch")
        _validate_payload_archive(payload_bytes, manifest_value)
    except (ValueError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        raise HTTPException(status_code=400, detail=str(error))
    target = _artifact_path(content_hash)
    if not target.is_dir():
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(
            tempfile.mkdtemp(prefix=f".{content_hash}-", dir=target.parent)
        )
        try:
            (temporary / "manifest.json").write_bytes(manifest_bytes)
            (temporary / "payload.zip").write_bytes(payload_bytes)
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
    return {"contentHash": content_hash}


@app.post(
    "/sandbox/execute",
    response_model=ExecutionResult,
    dependencies=[Depends(authenticate_service)],
)
async def execute_bundle(request: DockerExecuteRequest) -> ExecutionResult:
    """Start one prepared bundle in a hardened Docker container."""
    try:
        return await manager.start(request)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))


@app.post(
    "/sandbox/continue",
    response_model=ExecutionResult,
    dependencies=[Depends(authenticate_service)],
)
async def continue_execution(request: ContinueExecutionRequest) -> ExecutionResult:
    """Continue the original Docker worker with new inputs."""
    try:
        return await manager.continue_session(request.executionId, request.defaults)
    except KeyError:
        raise HTTPException(status_code=404, detail="Execution not found")


@app.post("/sandbox/terminate", dependencies=[Depends(authenticate_service)])
async def terminate_execution(request: TerminateExecutionRequest) -> dict:
    """Terminate one Docker worker idempotently."""
    await manager.terminate_session(request.executionId)
    return {"status": "terminated"}


def _safe_relative_path(raw_path: str) -> str:
    """Return a normalized safe POSIX path for cache/container operations."""
    path = PurePosixPath(raw_path)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("Unsafe relative path")
    return path.as_posix()


def _artifact_path(content_hash: str) -> Path:
    """Return the remote content-addressed artifact cache directory."""
    return _ARTIFACT_ROOT / content_hash[:2] / content_hash


def _bundle_path(bundle_hash: str) -> Path:
    """Return the remote content-addressed bundle cache directory."""
    return _BUNDLE_ROOT / bundle_hash[:2] / bundle_hash


def _validate_payload_archive(payload: bytes, manifest: dict) -> None:
    """Validate archive members exactly match the immutable file manifest."""
    expected = {file["path"]: file for file in manifest.get("files", [])}
    total_size = 0
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        actual_names = set()
        for info in archive.infolist():
            name = _safe_relative_path(info.filename)
            file_mode = info.external_attr >> 16
            if stat.S_ISLNK(file_mode):
                raise ValueError("Artifact cannot contain symbolic links")
            if name in actual_names or name not in expected:
                raise ValueError("Artifact archive member mismatch")
            content = archive.read(info)
            total_size += len(content)
            expected_file = expected[name]
            if len(content) != expected_file["size"]:
                raise ValueError("Artifact file size mismatch")
            if hashlib.sha256(content).hexdigest() != expected_file["sha256"]:
                raise ValueError("Artifact file hash mismatch")
            actual_names.add(name)
        if actual_names != set(expected):
            raise ValueError("Artifact archive is incomplete")
    if total_size > app_config.calc_report_max_total_size:
        raise ValueError("Artifact uncompressed size exceeds limit")


def _assemble_remote_bundle(bundle_hash: str, manifest: dict) -> Path:
    """Assemble instrumented code and SOURCE resources from remote cache."""
    target = _bundle_path(bundle_hash)
    if (target / "manifest.json").is_file():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{bundle_hash}-", dir=target.parent))
    try:
        for component in manifest["components"]:
            if component["isEntry"]:
                base = temporary
            else:
                base = (
                    temporary
                    / "__uzon_deps__"
                    / component["scopeKey"]
                    / component["alias"]
                    / component["selectorKey"]
                )
                _create_package_markers(base, temporary)
            _extract_component_artifact(
                component["executionArtifactHash"],
                base,
                is_entry=component["isEntry"],
                code=True,
            )
            _extract_component_artifact(
                component["sourceArtifactHash"],
                base,
                is_entry=component["isEntry"],
                code=False,
            )
        (temporary / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return target


def _extract_component_artifact(
    content_hash: str, base: Path, *, is_entry: bool, code: bool
) -> None:
    """Extract selected code or resource members into one component mount."""
    with zipfile.ZipFile(_artifact_path(content_hash) / "payload.zip") as archive:
        for name in archive.namelist():
            is_source_path = name.startswith("src/")
            if code != is_source_path:
                continue
            relative = Path(name)
            if code and not is_entry:
                relative = Path(*relative.parts[1:])
            destination = base / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(name))


def _create_package_markers(base: Path, root: Path) -> None:
    """Create missing dependency namespace package marker files."""
    current = base
    while current != root:
        current.mkdir(parents=True, exist_ok=True)
        marker = current / "__init__.py"
        if not marker.exists():
            marker.write_text("", encoding="utf-8")
        current = current.parent


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
