"""Remote Docker sandbox client using artifact-aware internal protocols."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from app.db.models.enums import ExecutorType
from app.service.calc_report_artifact_service import artifact_store
from config import app_config

from .backend_types import (
    PreparedExecutionBundle,
    RuntimeDescriptor,
    SandboxBackendMode,
)
from .execution_result import ExecutionResult
from .executor_interface import ISandboxExecutor


class RemoteDockerSandboxExecutor(ISandboxExecutor):
    """Prepare cached artifacts and execute bundles through a Docker service."""

    def __init__(self) -> None:
        """Initialize a lazy authenticated HTTP client."""
        self._client: httpx.AsyncClient | None = None
        self._descriptor: RuntimeDescriptor | None = None

    async def runtime_descriptor(self) -> RuntimeDescriptor:
        """Fetch and cache the remote image/toolchain capability descriptor."""
        if self._descriptor is not None:
            return self._descriptor
        response = await (await self._get_client()).get("/sandbox/health")
        response.raise_for_status()
        payload = response.json()
        image_digest = payload.get("runtimeImageDigest")
        if not image_digest:
            raise RuntimeError("Docker sandbox did not report a runtime image digest")
        self._descriptor = RuntimeDescriptor(
            mode=SandboxBackendMode.DOCKER,
            fingerprint=payload["runtimeFingerprint"],
            executor_type=ExecutorType.DOCKER,
            image_digest=image_digest,
            node_id=payload.get("nodeId"),
        )
        return self._descriptor

    async def execute_bundle(
        self,
        bundle: PreparedExecutionBundle,
        defaults: dict[str, dict[str, Any]] | None = None,
        is_silent: bool = False,
    ) -> ExecutionResult:
        """Upload only missing artifacts, prepare the bundle, and start Docker."""
        client = await self._get_client()
        await self._prepare_bundle(client, bundle)
        response = await client.post(
            "/sandbox/execute",
            json={
                "bundleHash": bundle.bundle_hash,
                "entryPath": bundle.entry_path,
                "defaults": defaults or {},
                "isSilent": is_silent,
            },
        )
        response.raise_for_status()
        return ExecutionResult.model_validate(response.json())

    async def continue_execution(
        self,
        execution_id: str,
        defaults: dict[str, dict[str, Any]],
    ) -> ExecutionResult:
        """Continue a remote Docker container session."""
        response = await (await self._get_client()).post(
            "/sandbox/continue",
            json={"executionId": execution_id, "defaults": defaults},
        )
        response.raise_for_status()
        return ExecutionResult.model_validate(response.json())

    async def terminate(self, execution_id: str) -> None:
        """Terminate a remote Docker session."""
        response = await (await self._get_client()).post(
            "/sandbox/terminate", json={"executionId": execution_id}
        )
        response.raise_for_status()

    async def close(self) -> None:
        """Close the shared HTTP connection pool."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Return a lazy client configured for the internal sandbox service."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=app_config.sandbox_remote_url.rstrip("/"),
                timeout=httpx.Timeout(app_config.sandbox_remote_timeout),
                headers={"Authorization": f"Bearer {app_config.sandbox_remote_token}"},
            )
        return self._client

    async def _prepare_bundle(
        self, client: httpx.AsyncClient, bundle: PreparedExecutionBundle
    ) -> None:
        """Satisfy remote artifact misses and atomically prepare the bundle."""
        response = await client.post(
            "/sandbox/bundles/prepare",
            json={
                "bundleHash": bundle.bundle_hash,
                "manifest": bundle.manifest,
            },
        )
        response.raise_for_status()
        missing_hashes = response.json().get("missingArtifacts", [])
        for content_hash in missing_hashes:
            artifact_dir = (
                artifact_store.root / "sha256" / content_hash[:2] / content_hash
            )
            manifest_path = artifact_dir / "manifest.json"
            payload_path = artifact_dir / "payload.zip"
            if not manifest_path.is_file() or not payload_path.is_file():
                raise RuntimeError(f"Local artifact cache is missing {content_hash}")
            with manifest_path.open("rb") as manifest_file, payload_path.open(
                "rb"
            ) as payload_file:
                upload = await client.put(
                    f"/sandbox/artifacts/{content_hash}",
                    files={
                        "manifest": (
                            "manifest.json",
                            manifest_file,
                            "application/json",
                        ),
                        "payload": (
                            "payload.zip",
                            payload_file,
                            "application/zip",
                        ),
                    },
                )
                upload.raise_for_status()
        if missing_hashes:
            final = await client.post(
                "/sandbox/bundles/prepare",
                json={"bundleHash": bundle.bundle_hash, "manifest": bundle.manifest},
            )
            final.raise_for_status()
            if final.json().get("missingArtifacts"):
                raise RuntimeError("Remote sandbox still reports missing artifacts")
