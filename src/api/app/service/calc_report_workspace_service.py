"""Atomic multi-file workspace operations for calculation reports."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import cast

import portalocker

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_state import (
    BuildStatus,
    PublishState,
    ReservedDependencySelectorKey,
    WorkspaceFileSource,
)
from app.controller.calc.calc_workspace_dto import (
    ReportDependencyDTO,
    WorkspaceDependenciesUpdateDTO,
    WorkspaceFileDTO,
    WorkspaceFileResDTO,
    WorkspaceResDTO,
    WorkspaceSaveDTO,
)
from app.calc_report_workspace_contract import (
    CALCBOOK_FORMAT_VERSION,
)
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_artifact import CalcReportArtifact
from app.db.models.calc_report_category import CalcReportCategory
from app.db.models.calc_report_dependency import (
    CalcReportDependency,
    CalcReportDependencySelector,
)
from app.db.models.calc_report_version import CalcReportVersion
from app.db.models.enums import ArtifactKind
from app.db.models.object_id import ObjectId
from app.exception.custom_exception import raise_ex
from app.service.calc_report_artifact_service import (
    ArtifactFile,
    ArtifactValidationError,
    artifact_store,
    is_importable_workspace_python_path,
    normalize_workspace_path,
    public_hash,
    sha256_text,
)
from app.service.calc_report_build_service import (
    configured_runtime_fingerprint_hint,
    get_build_state,
)
from config import app_config


def parse_version_name(version_name: str) -> tuple[int, int, int]:
    """Parse a strict semantic version used by report APIs.

    Args:
        version_name: Version in ``MAJOR.MINOR.PATCH`` form.

    Returns:
        Major, minor, and patch integers.

    Raises:
        ValueError: If the version is not a strict nonnegative semantic version.
    """
    parts = version_name.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError("versionName must use MAJOR.MINOR.PATCH")
    values = tuple(int(part) for part in parts)
    if any(str(value) != part for value, part in zip(values, parts, strict=True)):
        raise ValueError("versionName cannot contain leading zeros")
    return cast(tuple[int, int, int], values)


async def get_owned_report(
    user_id: int,
    report_oid: str,
    session: AsyncSession,
    *,
    include_deleted: bool = False,
) -> CalcReport:
    """Load an owned report by OID.

    Args:
        user_id: Current user database ID.
        report_oid: Public report identifier.
        session: Database session.
        include_deleted: Whether soft-deleted reports are eligible.

    Returns:
        Matching report model.

    Raises:
        CustomException: If the OID or report is invalid.
    """
    if not ObjectId.is_valid(report_oid):
        raise_ex(
            "Invalid report identifier",
            code=400,
            error_code=CalcErrorCode.INVALID_OBJECT_ID,
        )
    conditions = [CalcReport.oid == report_oid, CalcReport.userId == user_id]
    if not include_deleted:
        conditions.append(CalcReport.deletedAt.is_(None))
    report = await session.scalar(select(CalcReport).where(*conditions))
    if report is None:
        raise_ex(
            "Report not found",
            code=404,
            error_code=CalcErrorCode.REPORT_NOT_FOUND,
        )
    return cast(CalcReport, report)


def require_editable_report(report: CalcReport) -> None:
    """Reject source mutations for application-level read-only reports.

    Args:
        report: Report targeted by a source mutation.

    Returns:
        None.

    Raises:
        CustomException: If the report's inherited policy forbids editing.
    """
    if not report.canEdit:
        raise_ex(
            "Report editing is not permitted",
            code=403,
            error_code=CalcErrorCode.SHARE_NOT_ALLOWED,
        )


async def save_workspace(
    user_id: int,
    report_oid: str,
    request: WorkspaceSaveDTO,
    uploaded_files: dict[str, bytes],
    session: AsyncSession,
) -> WorkspaceResDTO:
    """Atomically replace a report workspace through optimistic concurrency.

    Args:
        user_id: Current user database ID.
        report_oid: Client-preallocated or existing report OID.
        request: Complete snapshot declaration.
        uploaded_files: Multipart file bytes keyed by workspace path.
        session: Database session.

    Returns:
        Saved workspace metadata.

    Raises:
        CustomException: If ownership, revision, manifest, or dependencies fail.
    """
    if not ObjectId.is_valid(report_oid):
        raise_ex(
            "Invalid report identifier",
            code=400,
            error_code=CalcErrorCode.INVALID_OBJECT_ID,
        )
    report = await session.scalar(
        select(CalcReport).where(
            CalcReport.oid == report_oid,
            CalcReport.userId == user_id,
            CalcReport.deletedAt.is_(None),
        )
    )
    if report is not None:
        require_editable_report(report)
    normalized_dependencies, dependency_models = await _resolve_dependencies(
        user_id, report, report_oid, request.dependencies, session
    )
    workspace_root = _workspace_path(user_id, report_oid)
    workspace_root.parent.mkdir(parents=True, exist_ok=True)
    lock_path = workspace_root.parent / ".workspace.lock"
    with portalocker.Lock(lock_path, timeout=30):
        if report is not None:
            await _refresh_workspace_manifest(report, workspace_root, session)
            if report.workspaceRevision != request.workspaceRevision:
                await session.rollback()
                raise_ex(
                    "Workspace was modified by another request",
                    code=409,
                    data={"expectedRevision": request.workspaceRevision},
                    error_code=CalcErrorCode.WORKSPACE_REVISION_CONFLICT,
                )
        temporary, workspace_manifest, calcbook = _stage_workspace_snapshot(
            workspace_root,
            request,
            uploaded_files,
            normalized_dependencies,
            report.workspaceManifest if report is not None else None,
        )
        workspace_hash = _workspace_content_hash(workspace_manifest)

        if report is None:
            if request.workspaceRevision != 0 or request.create is None:
                shutil.rmtree(temporary, ignore_errors=True)
                raise_ex(
                    "First workspace save requires report metadata and revision zero",
                    code=409,
                    error_code=CalcErrorCode.WORKSPACE_REVISION_CONFLICT,
                )
            category = await session.scalar(
                select(CalcReportCategory).where(
                    CalcReportCategory.oid == request.create.categoryOid,
                    CalcReportCategory.userId == user_id,
                    CalcReportCategory.deletedAt.is_(None),
                )
            )
            if category is None:
                shutil.rmtree(temporary, ignore_errors=True)
                raise_ex(
                    "Category not found",
                    code=404,
                    error_code=CalcErrorCode.CATEGORY_NOT_FOUND,
                )
            report = CalcReport(
                oid=report_oid,
                userId=user_id,
                categoryId=category.id,
                name=request.create.name.strip(),
                description=request.create.description,
                cover=request.create.cover,
                entryPath=calcbook["entryPath"],
                formatVersion=calcbook["formatVersion"],
                workspaceRevision=1,
                workspaceHash=workspace_hash,
                workspaceManifest=workspace_manifest,
            )
            session.add(report)
            await session.flush()
        else:
            if request.create is not None:
                shutil.rmtree(temporary, ignore_errors=True)
                raise_ex(
                    "Report metadata is only accepted on the first workspace save",
                    code=400,
                    error_code=CalcErrorCode.WORKSPACE_INVALID,
                )
            report.workspaceRevision += 1
            report.workspaceHash = workspace_hash
            report.workspaceManifest = workspace_manifest
            report.workspaceArtifactId = None
            report.entryPath = calcbook["entryPath"]
            report.formatVersion = calcbook["formatVersion"]

        backup = workspace_root.with_name(".workspace.previous")
        backup_created = False
        workspace_replaced = False
        try:
            if backup.exists():
                shutil.rmtree(backup)
            if workspace_root.exists():
                os.replace(workspace_root, backup)
                backup_created = True
            os.replace(temporary, workspace_root)
            workspace_replaced = True
            await _replace_dependencies(report.id, dependency_models, session)
            await session.commit()
        except Exception:
            await session.rollback()
            if workspace_replaced and workspace_root.exists():
                shutil.rmtree(workspace_root)
            if backup_created and backup.exists():
                os.replace(backup, workspace_root)
            raise
        finally:
            if temporary.exists():
                shutil.rmtree(temporary, ignore_errors=True)
        if backup.exists():
            shutil.rmtree(backup)

    await session.refresh(report)
    return await _workspace_response(report, session)


async def get_workspace(
    user_id: int, report_oid: str, session: AsyncSession
) -> WorkspaceResDTO:
    """Return the current owned workspace metadata without file contents."""
    report = await get_owned_report(user_id, report_oid, session)
    workspace_root = _workspace_path(user_id, report_oid)
    if not workspace_root.is_dir():
        raise_ex(
            "Workspace not found",
            code=404,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
    with portalocker.Lock(workspace_root.parent / ".workspace.lock", timeout=30):
        await _refresh_workspace_manifest(report, workspace_root, session)
    return await _workspace_response(report, session)


async def get_workspace_file(
    user_id: int,
    report_oid: str,
    file_path: str,
    session: AsyncSession,
) -> bytes:
    """Return one file from the current owned workspace artifact."""
    await get_owned_report(user_id, report_oid, session)
    workspace_root = _workspace_path(user_id, report_oid)
    if not workspace_root.is_dir():
        raise_ex(
            "Workspace not found",
            code=404,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
    try:
        normalized = normalize_workspace_path(file_path)
        candidate = (workspace_root / normalized).resolve()
        if (
            not candidate.is_relative_to(workspace_root.resolve())
            or not candidate.is_file()
        ):
            raise FileNotFoundError(normalized)
        return candidate.read_bytes()
    except (ArtifactValidationError, FileNotFoundError):
        raise_ex(
            "Workspace file not found",
            code=404,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )


async def replace_workspace_dependencies(
    user_id: int,
    report_oid: str,
    request: WorkspaceDependenciesUpdateDTO,
    session: AsyncSession,
) -> WorkspaceResDTO:
    """Replace dependency declarations while retaining all workspace files.

    Args:
        user_id: Current user database ID.
        report_oid: Owned report identifier.
        request: Dependency declarations and expected workspace revision.
        session: Database session.

    Returns:
        Updated workspace metadata.

    Raises:
        CustomException: If the workspace is absent or revision validation fails.
    """
    report = await get_owned_report(user_id, report_oid, session)
    if not _workspace_path(user_id, report_oid).is_dir():
        raise_ex(
            "Workspace not found",
            code=404,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
    file_descriptors = [
        WorkspaceFileDTO(
            path=file_info["path"],
            sha256=public_hash(file_info["sha256"]),
            source=WorkspaceFileSource.CURRENT,
        )
        for file_info in (report.workspaceManifest or {}).get("files", [])
    ]
    save_request = WorkspaceSaveDTO(
        workspaceRevision=request.workspaceRevision,
        files=file_descriptors,
        dependencies=request.dependencies,
    )
    return await save_workspace(user_id, report_oid, save_request, {}, session)


async def restore_workspace_artifact(
    user_id: int,
    report: CalcReport,
    artifact: CalcReportArtifact,
    session: AsyncSession,
) -> WorkspaceResDTO:
    """Replace mutable workspace state from an immutable SOURCE artifact.

    Args:
        user_id: Current user database ID.
        report: Owned report being restored.
        artifact: Version-bound SOURCE artifact.
        session: Database session.

    Returns:
        Restored workspace response.

    Raises:
        CustomException: If the artifact dependency snapshot is no longer valid.
    """
    require_editable_report(report)
    dependencies = [
        ReportDependencyDTO.model_validate(value)
        for value in artifact.manifest.get("dependencies", [])
    ]
    _, dependency_models = await _resolve_dependencies(
        user_id, report, report.oid, dependencies, session
    )
    target = _workspace_path(user_id, report.oid)
    with portalocker.Lock(target.parent / ".workspace.lock", timeout=30):
        materialize_workspace_artifact(user_id, report, artifact)
    report.workspaceRevision += 1
    await _replace_dependencies(report.id, dependency_models, session)
    await session.commit()
    await session.refresh(report)
    return await _workspace_response(report, session)


def _workspace_path(user_id: int, report_oid: str) -> Path:
    """Return the authoritative workspace directory for one owned report."""
    return (
        Path(app_config.calc_report_reports_root)
        / str(user_id)
        / report_oid
        / "workspace"
    ).resolve()


def _workspace_content_hash(manifest: dict) -> str:
    """Hash the canonical SOURCE manifest while excluding filesystem metadata."""
    canonical_manifest = {
        "formatVersion": 1,
        "artifactKind": "source",
        "calcbook": manifest["calcbook"],
        "dependencies": manifest.get("dependencies", []),
        "files": [
            {key: file_info[key] for key in ("path", "size", "sha256")}
            for file_info in manifest.get("files", [])
        ],
    }
    canonical = json.dumps(
        canonical_manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_text(canonical)


def _stage_workspace_snapshot(
    workspace_root: Path,
    request: WorkspaceSaveDTO,
    uploaded_files: dict[str, bytes],
    dependencies: list[dict],
    current_manifest: dict | None,
) -> tuple[Path, dict, dict]:
    """Build and validate a complete sibling workspace without publishing an artifact."""
    temporary = Path(
        tempfile.mkdtemp(prefix=".workspace-staging-", dir=workspace_root.parent)
    )
    current_files = {
        value["path"]: value for value in (current_manifest or {}).get("files", [])
    }
    declared_paths: set[str] = set()
    total_size = 0
    try:
        for descriptor in request.files:
            path = normalize_workspace_path(descriptor.path)
            if path in declared_paths:
                raise ArtifactValidationError(f"Duplicate workspace path: {path}")
            declared_paths.add(path)
            destination = temporary / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            if descriptor.source is WorkspaceFileSource.UPLOAD:
                if path not in uploaded_files:
                    raise ArtifactValidationError(f"Missing workspace upload: {path}")
                content = uploaded_files[path]
                if descriptor.sha256 and sha256_text(
                    content
                ) != descriptor.sha256.removeprefix("sha256:"):
                    raise ArtifactValidationError(
                        f"Workspace file hash mismatch: {path}"
                    )
                destination.write_bytes(content)
            else:
                source = workspace_root / path
                file_info = current_files.get(path)
                if file_info is None or not source.is_file():
                    raise ArtifactValidationError(
                        f"Current workspace file is missing: {path}"
                    )
                if descriptor.sha256 and file_info[
                    "sha256"
                ] != descriptor.sha256.removeprefix("sha256:"):
                    raise ArtifactValidationError(
                        f"Workspace file hash mismatch: {path}"
                    )
                try:
                    os.link(source, destination)
                except OSError:
                    shutil.copy2(source, destination)
            file_size = destination.stat().st_size
            if file_size > app_config.calc_report_max_file_size:
                raise ArtifactValidationError(f"Workspace file is too large: {path}")
            total_size += file_size
        unexpected_uploads = set(uploaded_files) - declared_paths
        if unexpected_uploads:
            raise ArtifactValidationError(
                f"Workspace contains undeclared uploads: {sorted(unexpected_uploads)}"
            )
        if len(declared_paths) > app_config.calc_report_max_file_count:
            raise ArtifactValidationError("Workspace contains too many files")
        if total_size > app_config.calc_report_max_total_size:
            raise ArtifactValidationError("Workspace total size exceeds the limit")
        manifest = _manifest_from_directory(
            temporary,
            dependencies,
            previous_files=current_files,
            ignore_ctime_changes=True,
            force_hash_paths={
                normalize_workspace_path(descriptor.path)
                for descriptor in request.files
                if descriptor.source is WorkspaceFileSource.UPLOAD
            },
        )
        return temporary, manifest, manifest["calcbook"]
    except (ArtifactValidationError, OSError) as error:
        shutil.rmtree(temporary, ignore_errors=True)
        raise_ex(
            "Workspace snapshot is invalid",
            code=400,
            data={"diagnostics": str(error)},
            error_code=CalcErrorCode.WORKSPACE_INVALID,
        )


def _manifest_from_directory(
    workspace_root: Path,
    dependencies: list[dict],
    *,
    previous_files: dict[str, dict] | None = None,
    force_hash_paths: set[str] | None = None,
    ignore_ctime_changes: bool = False,
) -> dict:
    """Scan one workspace into a validated logical SOURCE manifest."""
    artifact_files: list[ArtifactFile] = []
    file_entries: list[dict] = []
    total_size = 0
    forced_hashes = force_hash_paths or set()
    for candidate in sorted(workspace_root.rglob("*")):
        if candidate.is_symlink() or (candidate.exists() and not candidate.is_file()):
            if candidate.is_dir() and not candidate.is_symlink():
                continue
            raise ArtifactValidationError("Workspace cannot contain symbolic links")
        if not candidate.is_file():
            continue
        relative_path = candidate.relative_to(workspace_root).as_posix()
        normalized = normalize_workspace_path(relative_path)
        stat_result = candidate.stat()
        file_size = stat_result.st_size
        if file_size > app_config.calc_report_max_file_size:
            raise ArtifactValidationError(f"Workspace file is too large: {normalized}")
        total_size += file_size
        previous = (previous_files or {}).get(normalized)
        can_reuse_hash = (
            previous is not None
            and normalized not in forced_hashes
            and previous.get("size") == file_size
            and previous.get("mtimeNs") == stat_result.st_mtime_ns
            and (
                ignore_ctime_changes
                or previous.get("ctimeNs") == stat_result.st_ctime_ns
            )
        )
        content = candidate.read_bytes() if normalized == "calcbook.json" else None
        content_hash = (
            previous["sha256"]
            if can_reuse_hash
            else sha256_text(content if content is not None else candidate.read_bytes())
        )
        if content is not None:
            artifact_files.append(ArtifactFile(normalized, content))
        file_entries.append(
            {
                "path": normalized,
                "size": file_size,
                "sha256": content_hash,
                "mtimeNs": stat_result.st_mtime_ns,
                "ctimeNs": stat_result.st_ctime_ns,
            }
        )
    if len(file_entries) > app_config.calc_report_max_file_count:
        raise ArtifactValidationError("Workspace contains too many files")
    if total_size > app_config.calc_report_max_total_size:
        raise ArtifactValidationError("Workspace total size exceeds the limit")
    try:
        calcbook_content = next(
            value.content for value in artifact_files if value.path == "calcbook.json"
        )
        calcbook = json.loads(calcbook_content.decode("utf-8"))
    except (StopIteration, UnicodeDecodeError, json.JSONDecodeError):
        raise ArtifactValidationError("calcbook.json must contain valid UTF-8 JSON")
    if not isinstance(calcbook, dict):
        raise ArtifactValidationError("calcbook.json must contain an object")
    format_version = calcbook.get("formatVersion")
    entry_path = calcbook.get("entryPath")
    if format_version != CALCBOOK_FORMAT_VERSION:
        raise ArtifactValidationError("calcbook formatVersion is not supported")
    if not isinstance(entry_path, str):
        raise ArtifactValidationError("calcbook entryPath is invalid")
    entry_path = normalize_workspace_path(entry_path)
    if not is_importable_workspace_python_path(entry_path):
        raise ArtifactValidationError(
            "calcbook entryPath must identify an importable Python file"
        )
    if entry_path not in {value["path"] for value in file_entries}:
        raise ArtifactValidationError(
            "calcbook entryPath does not exist in the workspace"
        )
    calcbook["formatVersion"] = format_version
    calcbook["entryPath"] = entry_path
    return {
        "formatVersion": 1,
        "calcbook": calcbook,
        "dependencies": dependencies,
        "files": file_entries,
    }


async def _refresh_workspace_manifest(
    report: CalcReport,
    workspace_root: Path,
    session: AsyncSession,
) -> bool:
    """Reconcile direct filesystem edits into database workspace metadata."""
    manifest = _manifest_from_directory(
        workspace_root,
        (report.workspaceManifest or {}).get("dependencies", []),
        previous_files={
            value["path"]: value
            for value in (report.workspaceManifest or {}).get("files", [])
        },
    )
    workspace_hash = _workspace_content_hash(manifest)
    if workspace_hash == report.workspaceHash:
        if manifest != report.workspaceManifest:
            report.workspaceManifest = manifest
            await session.commit()
        return False
    report.workspaceRevision += 1
    report.workspaceHash = workspace_hash
    report.workspaceManifest = manifest
    report.workspaceArtifactId = None
    report.entryPath = manifest["calcbook"]["entryPath"]
    report.formatVersion = manifest["calcbook"]["formatVersion"]
    await session.commit()
    return True


async def ensure_workspace_artifact(
    user_id: int,
    report: CalcReport,
    session: AsyncSession,
) -> CalcReportArtifact:
    """Freeze the current authoritative workspace into a reusable SOURCE artifact."""
    workspace_root = _workspace_path(user_id, report.oid)
    if not workspace_root.is_dir():
        raise_ex(
            "Workspace not found",
            code=404,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
    with portalocker.Lock(workspace_root.parent / ".workspace.lock", timeout=30):
        await _refresh_workspace_manifest(report, workspace_root, session)
        if report.workspaceArtifactId is not None:
            artifact = await session.get(CalcReportArtifact, report.workspaceArtifactId)
            if artifact is not None and artifact.contentHash == report.workspaceHash:
                return artifact
        manifest = report.workspaceManifest or {}
        files = [
            ArtifactFile(value["path"], (workspace_root / value["path"]).read_bytes())
            for value in manifest.get("files", [])
        ]
        published = artifact_store.publish_source(
            files,
            manifest["calcbook"],
            manifest.get("dependencies", []),
        )
        artifact = await _get_or_create_source_artifact(published, session)
        report.workspaceArtifactId = artifact.id
        await session.commit()
        return artifact


async def _resolve_dependencies(
    user_id: int,
    report: CalcReport | None,
    report_oid: str,
    dependencies: list[ReportDependencyDTO],
    session: AsyncSession,
) -> tuple[
    list[dict], list[tuple[CalcReport, ReportDependencyDTO, dict[str, int | None]]]
]:
    """Resolve dependency OIDs/version names and validate the report graph."""
    aliases = [dependency.alias for dependency in dependencies]
    if len(aliases) != len(set(aliases)):
        raise_ex(
            "Dependency alias must be unique",
            code=400,
            error_code=CalcErrorCode.DEPENDENCY_INVALID,
        )
    normalized: list[dict] = []
    models: list[tuple[CalcReport, ReportDependencyDTO, dict[str, int | None]]] = []
    for dependency in dependencies:
        if dependency.targetReportOid == report_oid:
            raise_ex(
                "Report cannot depend on itself",
                code=400,
                error_code=CalcErrorCode.DEPENDENCY_INVALID,
            )
        target = await session.scalar(
            select(CalcReport).where(
                CalcReport.oid == dependency.targetReportOid,
                CalcReport.userId == user_id,
                CalcReport.deletedAt.is_(None),
            )
        )
        if target is None:
            raise_ex(
                "Dependency report not found",
                code=404,
                error_code=CalcErrorCode.DEPENDENCY_INVALID,
            )
        version_ids: dict[str, int | None] = {}
        normalized_selectors: list[dict] = []
        for selector in dependency.selectors:
            target_version_id = None
            if selector.selectorKey == ReservedDependencySelectorKey.LATEST:
                if target.latestVersionId is None:
                    raise_ex(
                        "Dependency latest version is not published",
                        code=400,
                        error_code=CalcErrorCode.DEPENDENCY_INVALID,
                    )
            else:
                try:
                    major, minor, patch = parse_version_name(selector.versionName or "")
                except ValueError as error:
                    raise_ex(
                        str(error),
                        code=400,
                        error_code=CalcErrorCode.DEPENDENCY_INVALID,
                    )
                version = await session.scalar(
                    select(CalcReportVersion).where(
                        CalcReportVersion.reportId == target.id,
                        CalcReportVersion.major == major,
                        CalcReportVersion.minor == minor,
                        CalcReportVersion.patch == patch,
                    )
                )
                if version is None:
                    raise_ex(
                        "Dependency version not found",
                        code=404,
                        error_code=CalcErrorCode.DEPENDENCY_INVALID,
                    )
                target_version_id = version.id
            version_ids[selector.selectorKey] = target_version_id
            normalized_selectors.append(
                {
                    "selectorKey": selector.selectorKey,
                    "versionName": selector.versionName,
                    "isDefault": selector.isDefault,
                }
            )
        normalized.append(
            {
                "alias": dependency.alias,
                "targetReportOid": target.oid,
                "selectors": normalized_selectors,
            }
        )
        models.append((target, dependency, version_ids))
    if report is not None:
        await _assert_dependency_graph_acyclic(
            report.id, [target.id for target, _, _ in models], session
        )
    return normalized, models


async def _assert_dependency_graph_acyclic(
    report_id: int, target_ids: list[int], session: AsyncSession
) -> None:
    """Reject dependency replacements that introduce a report cycle."""
    rows = (
        await session.execute(
            select(
                CalcReportDependency.reportId,
                CalcReportDependency.targetReportId,
            )
        )
    ).all()
    graph: dict[int, set[int]] = {}
    for source_id, target_id in rows:
        graph.setdefault(source_id, set()).add(target_id)
    graph[report_id] = set(target_ids)

    def reaches_source(node_id: int, visited: set[int]) -> bool:
        """Return whether one target can reach the report being replaced."""
        if node_id == report_id:
            return True
        if node_id in visited:
            return False
        visited.add(node_id)
        return any(reaches_source(child, visited) for child in graph.get(node_id, ()))

    if any(reaches_source(target_id, set()) for target_id in target_ids):
        raise_ex(
            "Dependency cycle detected",
            code=400,
            error_code=CalcErrorCode.DEPENDENCY_CYCLE,
        )


async def _get_or_create_source_artifact(published, session: AsyncSession):
    """Return the database row for a published SOURCE artifact."""
    artifact = await session.scalar(
        select(CalcReportArtifact).where(
            CalcReportArtifact.contentHash == published.content_hash
        )
    )
    if artifact is None:
        try:
            async with session.begin_nested():
                artifact = CalcReportArtifact(
                    artifactKind=ArtifactKind.SOURCE.value,
                    contentHash=published.content_hash,
                    storageKey=published.storage_key,
                    manifest=published.manifest,
                    fileCount=published.file_count,
                    totalSize=published.total_size,
                    formatVersion=1,
                )
                session.add(artifact)
                await session.flush()
        except IntegrityError:
            artifact = await session.scalar(
                select(CalcReportArtifact).where(
                    CalcReportArtifact.contentHash == published.content_hash
                )
            )
            if artifact is None:
                raise
    return artifact


async def _replace_dependencies(
    report_id: int,
    dependency_models: list[
        tuple[CalcReport, ReportDependencyDTO, dict[str, int | None]]
    ],
    session: AsyncSession,
) -> None:
    """Replace all mutable dependency rows in the current transaction."""
    await session.execute(
        delete(CalcReportDependency).where(CalcReportDependency.reportId == report_id)
    )
    await session.flush()
    for target, declaration, version_ids in dependency_models:
        dependency = CalcReportDependency(
            reportId=report_id, targetReportId=target.id, alias=declaration.alias
        )
        session.add(dependency)
        await session.flush()
        for selector in declaration.selectors:
            session.add(
                CalcReportDependencySelector(
                    dependencyId=dependency.id,
                    targetReportId=target.id,
                    selectorKey=selector.selectorKey,
                    targetVersionId=version_ids[selector.selectorKey],
                    isDefault=selector.isDefault,
                )
            )


def materialize_workspace_artifact(
    user_id: int, report: CalcReport, artifact: CalcReportArtifact
) -> dict:
    """Replace an authoritative workspace from one immutable SOURCE artifact.

    Args:
        user_id: Workspace owner database ID.
        report: Report whose workspace is replaced.
        artifact: Immutable SOURCE artifact to materialize.

    Returns:
        Filesystem-aware workspace manifest stored on the report.

    Raises:
        OSError: If the artifact cannot be materialized.
        ArtifactValidationError: If the restored workspace is invalid.
    """
    target = _workspace_path(user_id, report.oid)
    artifact_store.materialize(artifact.storageKey, target)
    manifest = _manifest_from_directory(
        target, artifact.manifest.get("dependencies", [])
    )
    report.workspaceArtifactId = artifact.id
    report.workspaceHash = _workspace_content_hash(manifest)
    report.workspaceManifest = manifest
    report.entryPath = manifest["calcbook"]["entryPath"]
    report.formatVersion = manifest["calcbook"]["formatVersion"]
    return manifest


async def _workspace_response(
    report: CalcReport, session: AsyncSession
) -> WorkspaceResDTO:
    """Build the public workspace response with derived states."""
    runtime_fingerprint = configured_runtime_fingerprint_hint()
    build_status = (
        (
            await get_build_state(
                report.workspaceArtifactId, runtime_fingerprint, session
            )
        )[0]
        if runtime_fingerprint is not None and report.workspaceArtifactId is not None
        else BuildStatus.NOT_REQUESTED
    )
    latest = (
        await session.get(CalcReportVersion, report.latestVersionId)
        if report.latestVersionId is not None
        else None
    )
    latest_artifact = (
        await session.get(CalcReportArtifact, latest.sourceArtifactId)
        if latest is not None
        else None
    )
    publish_state = (
        PublishState.PUBLISHED
        if latest_artifact is not None
        and latest_artifact.contentHash == report.workspaceHash
        else (
            PublishState.UNPUBLISHED_CHANGES
            if latest is not None
            else PublishState.UNPUBLISHED
        )
    )
    manifest = report.workspaceManifest or {}
    files = [
        WorkspaceFileResDTO(
            path=file_info["path"],
            size=file_info["size"],
            sha256=public_hash(file_info["sha256"]),
        )
        for file_info in manifest.get("files", [])
    ]
    dependencies = [
        ReportDependencyDTO.model_validate(dependency)
        for dependency in manifest.get("dependencies", [])
    ]
    return WorkspaceResDTO(
        reportOid=report.oid,
        workspaceRevision=report.workspaceRevision,
        workspaceHash=public_hash(report.workspaceHash or ""),
        entryPath=report.entryPath,
        formatVersion=report.formatVersion,
        files=files,
        dependencies=dependencies,
        buildStatus=build_status,
        publishState=publish_state,
    )
