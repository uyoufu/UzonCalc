"""Content-addressed artifact storage for calculation reports."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

from app.calc_report_workspace_contract import (
    CALCBOOK_FORMAT_VERSION,
    CALCBOOK_PATH,
    ROOT_PACKAGE_PATH,
    RESERVED_RUNTIME_ROOTS,
)
from app.controller.calc.calc_state import ArtifactManifestKind
from config import app_config

_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class ArtifactValidationError(ValueError):
    """Report an invalid or unsafe workspace artifact."""


@dataclass(frozen=True)
class ArtifactFile:
    """Hold one normalized artifact file before publication."""

    path: str
    content: bytes


@dataclass(frozen=True)
class PublishedArtifact:
    """Describe a content-addressed artifact published on disk."""

    content_hash: str
    storage_key: str
    manifest: dict
    file_count: int
    total_size: int


def normalize_workspace_path(raw_path: str) -> str:
    """Normalize and validate one workspace-relative POSIX path.

    Args:
        raw_path: Untrusted path supplied by an API client or archive.

    Returns:
        Canonical POSIX path.

    Raises:
        ArtifactValidationError: If the path escapes or violates workspace layout.
    """
    if not raw_path or "\\" in raw_path or "\x00" in raw_path:
        raise ArtifactValidationError("Workspace path is invalid")
    path = PurePosixPath(raw_path)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ArtifactValidationError("Workspace path must be normalized and relative")
    if path.parts[0] in RESERVED_RUNTIME_ROOTS:
        raise ArtifactValidationError("Workspace path is reserved by the runtime")
    return path.as_posix()


def is_importable_workspace_python_path(path: str) -> bool:
    """Return whether a root-relative path identifies a Python module.

    Args:
        path: Normalized workspace-relative path.

    Returns:
        Whether the path ends in ``.py`` and every module segment is valid.

    Raises:
        None.
    """
    pure_path = PurePosixPath(path)
    return pure_path.suffix == ".py" and all(
        part.isidentifier() for part in pure_path.with_suffix("").parts
    )


def sha256_text(content: bytes) -> str:
    """Return the lowercase SHA-256 digest for bytes."""
    return hashlib.sha256(content).hexdigest()


def public_hash(content_hash: str) -> str:
    """Format a database hash for public API responses."""
    return f"sha256:{content_hash}"


class ArtifactStore:
    """Publish, read, and materialize immutable artifact payloads."""

    def __init__(self, root: Path | None = None):
        """Initialize the store.

        Args:
            root: Optional artifact root used by tests or alternate deployments.
        """
        self.root = root or Path(app_config.calc_report_artifacts_root)

    def publish_source(
        self,
        files: Iterable[ArtifactFile],
        calcbook: dict,
        dependencies: list[dict],
    ) -> PublishedArtifact:
        """Validate and atomically publish a SOURCE artifact.

        Args:
            files: Complete workspace file set.
            calcbook: Parsed calculation-book manifest.
            dependencies: Normalized immutable dependency declarations.

        Returns:
            Published content-addressed artifact metadata.

        Raises:
            ArtifactValidationError: If paths, sizes, or required files are invalid.
            OSError: If artifact storage cannot be written.
        """
        normalized_files = self._validate_files(files)
        self._validate_calcbook(normalized_files, calcbook)
        file_manifest = [
            {
                "path": artifact_file.path,
                "size": len(artifact_file.content),
                "sha256": sha256_text(artifact_file.content),
            }
            for artifact_file in normalized_files
        ]
        manifest = {
            "formatVersion": 1,
            "artifactKind": ArtifactManifestKind.SOURCE,
            "calcbook": calcbook,
            "dependencies": dependencies,
            "files": file_manifest,
        }
        canonical_manifest = json.dumps(
            manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        content_hash = sha256_text(canonical_manifest)
        storage_key = f"sha256/{content_hash[:2]}/{content_hash}"
        artifact_dir = self.root / storage_key
        if not artifact_dir.is_dir():
            self._write_artifact(artifact_dir, manifest, normalized_files)
        return PublishedArtifact(
            content_hash=content_hash,
            storage_key=storage_key,
            manifest=manifest,
            file_count=len(normalized_files),
            total_size=sum(len(item.content) for item in normalized_files),
        )

    def publish_instrumented(
        self,
        files: Iterable[ArtifactFile],
        *,
        source_hash: str,
        runtime_fingerprint: str,
        source_maps: dict[str, list[dict]],
    ) -> PublishedArtifact:
        """Atomically publish derived executable Python files.

        Args:
            files: Instrumented Python files preserving the SOURCE tree shape.
            source_hash: SOURCE artifact hash used for derivation.
            runtime_fingerprint: Exact compatible toolchain/runtime fingerprint.
            source_maps: Per-file generated/original line mappings.

        Returns:
            Published INSTRUMENTED artifact metadata.

        Raises:
            ArtifactValidationError: If a generated path or file is invalid.
        """
        normalized_files: list[ArtifactFile] = []
        seen_paths: set[str] = set()
        total_size = 0
        for artifact_file in files:
            normalized_path = normalize_workspace_path(artifact_file.path)
            if not normalized_path.endswith(".py"):
                raise ArtifactValidationError("Instrumented path must be a Python file")
            if normalized_path in seen_paths:
                raise ArtifactValidationError("Duplicate instrumented path")
            seen_paths.add(normalized_path)
            total_size += len(artifact_file.content)
            normalized_files.append(
                ArtifactFile(normalized_path, artifact_file.content)
            )
        normalized_files.sort(key=lambda item: item.path)
        file_manifest = [
            {
                "path": item.path,
                "size": len(item.content),
                "sha256": sha256_text(item.content),
            }
            for item in normalized_files
        ]
        manifest = {
            "formatVersion": 1,
            "artifactKind": ArtifactManifestKind.INSTRUMENTED,
            "sourceArtifactHash": source_hash,
            "runtimeFingerprint": runtime_fingerprint,
            "sourceMaps": source_maps,
            "files": file_manifest,
        }
        canonical = json.dumps(
            manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        content_hash = sha256_text(canonical)
        storage_key = f"sha256/{content_hash[:2]}/{content_hash}"
        artifact_dir = self.root / storage_key
        if not artifact_dir.is_dir():
            self._write_artifact(artifact_dir, manifest, normalized_files)
        return PublishedArtifact(
            content_hash=content_hash,
            storage_key=storage_key,
            manifest=manifest,
            file_count=len(normalized_files),
            total_size=total_size,
        )

    def read_file(self, storage_key: str, relative_path: str) -> bytes:
        """Read one file from an immutable artifact payload.

        Args:
            storage_key: Database-relative artifact storage key.
            relative_path: Workspace-relative file path.

        Returns:
            File bytes.

        Raises:
            KeyError: If the file is absent.
            ArtifactValidationError: If the requested path is unsafe.
        """
        normalized_path = normalize_workspace_path(relative_path)
        payload_path = self.root / storage_key / "payload.zip"
        try:
            with zipfile.ZipFile(payload_path) as archive:
                return archive.read(normalized_path)
        except KeyError as error:
            raise KeyError(normalized_path) from error

    def read_all(self, storage_key: str) -> list[ArtifactFile]:
        """Read every file from an artifact in stable path order."""
        payload_path = self.root / storage_key / "payload.zip"
        with zipfile.ZipFile(payload_path) as archive:
            return [
                ArtifactFile(path=name, content=archive.read(name))
                for name in sorted(archive.namelist())
            ]

    def materialize(self, storage_key: str, target: Path) -> None:
        """Atomically replace a readable workspace/version projection.

        Args:
            storage_key: Database-relative artifact storage key.
            target: Projection directory to replace.

        Raises:
            OSError: If projection files cannot be written or replaced.
        """
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = Path(tempfile.mkdtemp(prefix=f".{target.name}-", dir=target.parent))
        try:
            for artifact_file in self.read_all(storage_key):
                destination = temp_dir / artifact_file.path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(artifact_file.content)
            backup = target.with_name(f".{target.name}.old")
            if backup.exists():
                shutil.rmtree(backup)
            if target.exists():
                os.replace(target, backup)
            os.replace(temp_dir, target)
            if backup.exists():
                shutil.rmtree(backup)
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _validate_files(self, files: Iterable[ArtifactFile]) -> list[ArtifactFile]:
        """Validate a complete workspace file set and return it sorted."""
        normalized_files: list[ArtifactFile] = []
        seen_paths: set[str] = set()
        total_size = 0
        for artifact_file in files:
            path = normalize_workspace_path(artifact_file.path)
            if path in seen_paths:
                raise ArtifactValidationError(f"Duplicate workspace path: {path}")
            file_size = len(artifact_file.content)
            if file_size > app_config.calc_report_max_file_size:
                raise ArtifactValidationError(f"Workspace file is too large: {path}")
            total_size += file_size
            seen_paths.add(path)
            normalized_files.append(
                ArtifactFile(path=path, content=artifact_file.content)
            )
        if len(normalized_files) > app_config.calc_report_max_file_count:
            raise ArtifactValidationError("Workspace contains too many files")
        if total_size > app_config.calc_report_max_total_size:
            raise ArtifactValidationError("Workspace total size exceeds the limit")
        if CALCBOOK_PATH not in seen_paths:
            raise ArtifactValidationError("calcbook.json is required")
        if ROOT_PACKAGE_PATH not in seen_paths:
            raise ArtifactValidationError("Workspace root __init__.py is required")
        for path in seen_paths:
            parts = PurePosixPath(path).parts
            ancestors = {
                PurePosixPath(*parts[:index]).as_posix()
                for index in range(1, len(parts))
            }
            if ancestors & seen_paths:
                raise ArtifactValidationError(
                    f"Workspace file cannot contain child paths: {path}"
                )
        return sorted(normalized_files, key=lambda item: item.path)

    def _validate_calcbook(
        self, files: list[ArtifactFile], calcbook: dict
    ) -> None:
        """Validate manifest metadata against the persisted calcbook file.

        Args:
            files: Complete normalized workspace file set.
            calcbook: Parsed calcbook metadata supplied by the caller.

        Returns:
            None.

        Raises:
            ArtifactValidationError: If metadata, file content, or entry is invalid.
        """
        calcbook_file = next(file for file in files if file.path == CALCBOOK_PATH)
        try:
            persisted_calcbook = json.loads(calcbook_file.content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ArtifactValidationError(
                "calcbook.json must contain valid UTF-8 JSON"
            ) from error
        if not isinstance(calcbook, dict) or persisted_calcbook != calcbook:
            raise ArtifactValidationError(
                "calcbook metadata does not match calcbook.json"
            )
        if calcbook.get("formatVersion") != CALCBOOK_FORMAT_VERSION:
            raise ArtifactValidationError("calcbook formatVersion is not supported")
        entry_path = calcbook.get("entryPath")
        if not isinstance(entry_path, str):
            raise ArtifactValidationError("calcbook entryPath is invalid")
        normalized_entry = normalize_workspace_path(entry_path)
        if not is_importable_workspace_python_path(normalized_entry):
            raise ArtifactValidationError(
                "calcbook entryPath must identify an importable Python file"
            )
        if normalized_entry not in {file.path for file in files}:
            raise ArtifactValidationError(
                "calcbook entryPath does not exist in the workspace"
            )

    def _write_artifact(
        self,
        artifact_dir: Path,
        manifest: dict,
        files: list[ArtifactFile],
    ) -> None:
        """Write an artifact through a sibling temporary directory."""
        artifact_dir.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = Path(
            tempfile.mkdtemp(prefix=f".{artifact_dir.name}-", dir=artifact_dir.parent)
        )
        try:
            (temp_dir / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            payload_buffer = io.BytesIO()
            with zipfile.ZipFile(
                payload_buffer, "w", compression=zipfile.ZIP_DEFLATED
            ) as archive:
                for artifact_file in files:
                    info = zipfile.ZipInfo(artifact_file.path, _ZIP_TIMESTAMP)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, artifact_file.content)
            (temp_dir / "payload.zip").write_bytes(payload_buffer.getvalue())
            try:
                os.replace(temp_dir, artifact_dir)
            except OSError:
                if not artifact_dir.is_dir():
                    raise
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)


artifact_store = ArtifactStore()
