"""Shared execution-backend contracts and runtime descriptors."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.db.models.enums import ExecutorType


class SandboxBackendMode(StrEnum):
    """Identify the configured managed calculation execution mechanism."""

    IN_PROCESS = "in_process"
    BUBBLEWRAP = "bubblewrap"
    DOCKER = "docker"


@dataclass(frozen=True)
class RuntimeDescriptor:
    """Describe an exact runtime used for build and bundle cache keys."""

    mode: SandboxBackendMode
    fingerprint: str
    executor_type: ExecutorType
    image_digest: str | None = None
    node_id: str | None = None


@dataclass(frozen=True)
class PreparedExecutionBundle:
    """Describe an assembled immutable bundle ready for one backend."""

    oid: str
    bundle_hash: str
    root: Path
    entry_path: str
    manifest: dict


def configured_backend_mode(raw_mode: str) -> SandboxBackendMode:
    """Parse a configured backend mode and reject retired aliases.

    Args:
        raw_mode: Value from application configuration.

    Returns:
        Valid backend enum.

    Raises:
        ValueError: If the mode is unsupported.
    """
    try:
        return SandboxBackendMode(raw_mode.strip().lower())
    except ValueError as error:
        supported = ", ".join(mode.value for mode in SandboxBackendMode)
        raise ValueError(f"sandbox.mode must be one of: {supported}") from error
