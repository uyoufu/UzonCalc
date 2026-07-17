"""Atomic multi-file workspace operations for calculation reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_state import (
    BuildStatus,
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
    normalize_workspace_path,
    public_hash,
    sha256_text,
)
from app.service.calc_report_build_service import (
    configured_runtime_fingerprint_hint,
    get_build_state,
)
from app.service.calc_report_state_service import resolve_publish_state
from config import app_config, logger


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
    current_artifact = None
    if report is not None and report.workspaceArtifactId is not None:
        current_artifact = await session.get(
            CalcReportArtifact, report.workspaceArtifactId
        )
    files = _resolve_snapshot_files(request, uploaded_files, current_artifact)
    calcbook = _parse_calcbook(files)
    normalized_dependencies, dependency_models = await _resolve_dependencies(
        user_id, report, report_oid, request.dependencies, session
    )
    try:
        published = artifact_store.publish_source(
            files, calcbook, normalized_dependencies
        )
    except ArtifactValidationError as error:
        raise_ex(
            "Workspace snapshot is invalid",
            code=400,
            data={"diagnostics": str(error)},
            error_code=CalcErrorCode.WORKSPACE_INVALID,
        )
    artifact = await _get_or_create_source_artifact(published, session)

    if report is None:
        if request.workspaceRevision != 0 or request.create is None:
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
            workspaceArtifactId=artifact.id,
        )
        session.add(report)
        await session.flush()
    else:
        if request.create is not None:
            raise_ex(
                "Report metadata is only accepted on the first workspace save",
                code=400,
                error_code=CalcErrorCode.WORKSPACE_INVALID,
            )
        result = await session.execute(
            update(CalcReport)
            .where(
                CalcReport.id == report.id,
                CalcReport.workspaceRevision == request.workspaceRevision,
                CalcReport.deletedAt.is_(None),
            )
            .values(
                workspaceRevision=CalcReport.workspaceRevision + 1,
                workspaceArtifactId=artifact.id,
                entryPath=calcbook["entryPath"],
                formatVersion=calcbook["formatVersion"],
            )
        )
        if result.rowcount != 1:
            await session.rollback()
            raise_ex(
                "Workspace was modified by another request",
                code=409,
                data={"expectedRevision": request.workspaceRevision},
                error_code=CalcErrorCode.WORKSPACE_REVISION_CONFLICT,
            )
        report.workspaceRevision = request.workspaceRevision + 1
        report.workspaceArtifactId = artifact.id
        report.entryPath = calcbook["entryPath"]
        report.formatVersion = calcbook["formatVersion"]

    await _replace_dependencies(report.id, dependency_models, session)
    await session.commit()
    await session.refresh(report)
    _materialize_workspace_projection(user_id, report, artifact)
    return await _workspace_response(report, artifact, session)


async def get_workspace(
    user_id: int, report_oid: str, session: AsyncSession
) -> WorkspaceResDTO:
    """Return the current owned workspace metadata without file contents."""
    report = await get_owned_report(user_id, report_oid, session)
    if report.workspaceArtifactId is None:
        raise_ex(
            "Workspace not found",
            code=404,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
    artifact = await session.get(CalcReportArtifact, report.workspaceArtifactId)
    if artifact is None:
        raise_ex(
            "Workspace artifact not found",
            code=500,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
    return await _workspace_response(report, artifact, session)


async def get_workspace_file(
    user_id: int,
    report_oid: str,
    file_path: str,
    session: AsyncSession,
) -> bytes:
    """Return one file from the current owned workspace artifact."""
    report = await get_owned_report(user_id, report_oid, session)
    if report.workspaceArtifactId is None:
        raise_ex(
            "Workspace not found",
            code=404,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
    artifact = await session.get(CalcReportArtifact, report.workspaceArtifactId)
    if artifact is None:
        raise_ex(
            "Workspace artifact not found",
            code=500,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
    try:
        return artifact_store.read_file(artifact.storageKey, file_path)
    except (ArtifactValidationError, KeyError):
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
    if report.workspaceArtifactId is None:
        raise_ex(
            "Workspace not found",
            code=404,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
    artifact = await session.get(CalcReportArtifact, report.workspaceArtifactId)
    if artifact is None:
        raise_ex(
            "Workspace artifact not found",
            code=500,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
    file_descriptors = [
        WorkspaceFileDTO(
            path=file_info["path"],
            sha256=public_hash(file_info["sha256"]),
            source=WorkspaceFileSource.CURRENT,
        )
        for file_info in artifact.manifest.get("files", [])
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
    dependencies = [
        ReportDependencyDTO.model_validate(value)
        for value in artifact.manifest.get("dependencies", [])
    ]
    _, dependency_models = await _resolve_dependencies(
        user_id, report, report.oid, dependencies, session
    )
    report.workspaceArtifactId = artifact.id
    report.workspaceRevision += 1
    report.entryPath = artifact.manifest["calcbook"]["entryPath"]
    report.formatVersion = artifact.manifest["calcbook"]["formatVersion"]
    await _replace_dependencies(report.id, dependency_models, session)
    await session.commit()
    await session.refresh(report)
    _materialize_workspace_projection(user_id, report, artifact)
    return await _workspace_response(report, artifact, session)


def _resolve_snapshot_files(
    request: WorkspaceSaveDTO,
    uploaded_files: dict[str, bytes],
    current_artifact: CalcReportArtifact | None,
) -> list[ArtifactFile]:
    """Resolve uploaded/reused descriptors into one complete file set."""
    descriptor_paths: set[str] = set()
    files: list[ArtifactFile] = []
    for descriptor in request.files:
        try:
            path = normalize_workspace_path(descriptor.path)
        except ArtifactValidationError as error:
            raise_ex(
                "Workspace snapshot is invalid",
                code=400,
                data={"path": descriptor.path, "diagnostics": str(error)},
                error_code=CalcErrorCode.WORKSPACE_INVALID,
            )
        if path in descriptor_paths:
            raise_ex(
                "Workspace contains duplicate paths",
                code=400,
                error_code=CalcErrorCode.WORKSPACE_INVALID,
            )
        descriptor_paths.add(path)
        if descriptor.source is WorkspaceFileSource.UPLOAD:
            if path not in uploaded_files:
                raise_ex(
                    "Workspace upload is missing a declared file",
                    code=400,
                    data={"path": path},
                    error_code=CalcErrorCode.WORKSPACE_INVALID,
                )
            content = uploaded_files[path]
        else:
            if current_artifact is None:
                raise_ex(
                    "Cannot reuse a file without an existing workspace",
                    code=400,
                    data={"path": path},
                    error_code=CalcErrorCode.WORKSPACE_INVALID,
                )
            try:
                content = artifact_store.read_file(current_artifact.storageKey, path)
            except KeyError:
                raise_ex(
                    "Reused workspace file does not exist",
                    code=400,
                    data={"path": path},
                    error_code=CalcErrorCode.WORKSPACE_INVALID,
                )
        if descriptor.sha256:
            expected_hash = descriptor.sha256.removeprefix("sha256:")
            if sha256_text(content) != expected_hash:
                raise_ex(
                    "Workspace file hash does not match its declaration",
                    code=400,
                    data={"path": path},
                    error_code=CalcErrorCode.WORKSPACE_INVALID,
                )
        files.append(ArtifactFile(path=path, content=content))
    unexpected_uploads = set(uploaded_files) - descriptor_paths
    if unexpected_uploads:
        raise_ex(
            "Workspace contains undeclared uploads",
            code=400,
            data={"paths": sorted(unexpected_uploads)},
            error_code=CalcErrorCode.WORKSPACE_INVALID,
        )
    return files


def _parse_calcbook(files: list[ArtifactFile]) -> dict:
    """Parse and validate the required calcbook.json contract."""
    file_map = {item.path: item.content for item in files}
    try:
        calcbook = json.loads(file_map["calcbook.json"].decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError):
        raise_ex(
            "calcbook.json must contain valid UTF-8 JSON",
            code=400,
            error_code=CalcErrorCode.WORKSPACE_INVALID,
        )
    if not isinstance(calcbook, dict):
        raise_ex(
            "calcbook.json must contain an object",
            code=400,
            error_code=CalcErrorCode.WORKSPACE_INVALID,
        )
    format_version = calcbook.get("formatVersion", 1)
    entry_path = calcbook.get("entryPath", "src/main.py")
    if not isinstance(format_version, int) or format_version < 1:
        raise_ex(
            "calcbook formatVersion must be a positive integer",
            code=400,
            error_code=CalcErrorCode.WORKSPACE_INVALID,
        )
    try:
        entry_path = normalize_workspace_path(entry_path)
    except (ArtifactValidationError, TypeError):
        raise_ex(
            "calcbook entryPath is invalid",
            code=400,
            error_code=CalcErrorCode.WORKSPACE_INVALID,
        )
    if not entry_path.startswith("src/") or not entry_path.endswith(".py"):
        raise_ex(
            "calcbook entryPath must point to a Python file under src",
            code=400,
            error_code=CalcErrorCode.WORKSPACE_INVALID,
        )
    if entry_path not in file_map:
        raise_ex(
            "calcbook entryPath does not exist in the workspace",
            code=400,
            error_code=CalcErrorCode.WORKSPACE_INVALID,
        )
    calcbook["formatVersion"] = format_version
    calcbook["entryPath"] = entry_path
    return calcbook


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


def _materialize_workspace_projection(
    user_id: int, report: CalcReport, artifact: CalcReportArtifact
) -> None:
    """Refresh the non-authoritative readable workspace projection."""
    target = (
        Path(app_config.calc_report_reports_root)
        / str(user_id)
        / report.oid
        / "workspace"
    )
    try:
        artifact_store.materialize(artifact.storageKey, target)
    except OSError:
        logger.exception("Failed to refresh workspace projection for %s", report.oid)


async def _workspace_response(
    report: CalcReport,
    artifact: CalcReportArtifact,
    session: AsyncSession,
) -> WorkspaceResDTO:
    """Build the public workspace response with derived states."""
    runtime_fingerprint = configured_runtime_fingerprint_hint()
    build_status = (
        (await get_build_state(artifact.id, runtime_fingerprint, session))[0]
        if runtime_fingerprint is not None
        else BuildStatus.NOT_REQUESTED
    )
    publish_state = await resolve_publish_state(report, artifact, session)
    files = [
        WorkspaceFileResDTO(
            path=file_info["path"],
            size=file_info["size"],
            sha256=public_hash(file_info["sha256"]),
        )
        for file_info in artifact.manifest.get("files", [])
    ]
    dependencies = [
        ReportDependencyDTO.model_validate(dependency)
        for dependency in artifact.manifest.get("dependencies", [])
    ]
    return WorkspaceResDTO(
        reportOid=report.oid,
        workspaceRevision=report.workspaceRevision,
        sourceArtifactHash=public_hash(artifact.contentHash),
        entryPath=report.entryPath,
        formatVersion=report.formatVersion,
        files=files,
        dependencies=dependencies,
        buildStatus=build_status,
        publishState=publish_state,
    )
