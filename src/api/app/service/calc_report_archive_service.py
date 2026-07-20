"""Export and import portable v3 calculation-report dependency closures."""

from __future__ import annotations

import datetime
import hashlib
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_share_dto import ShareImportDTO, ShareImportResDTO
from app.controller.calc.calc_workspace_dto import ReportDependencyDTO
from app.db.models.calc_report import CalcReport, CalcReportOrigin, CalcReportSyncSource
from app.db.models.calc_report_artifact import CalcReportArtifact
from app.db.models.calc_report_category import CalcReportCategory
from app.db.models.calc_report_version import CalcReportVersion
from app.db.models.enums import ReportOriginType
from app.exception.custom_exception import raise_ex
from app.service.calc_report_artifact_service import ArtifactFile, artifact_store
from app.service.calc_report_service import write_latest_projection
from app.service.calc_report_share_service import (
    SharedVersionNode,
    _available_report_name,
    _collect_shared_closure,
)
from app.service.calc_report_version_service import _materialize_version_projection
from app.service.calc_report_workspace_service import (
    _get_or_create_source_artifact,
    _materialize_workspace_projection,
    _replace_dependencies,
    _resolve_dependencies,
)
from app.service.secret_storage_service import encrypt_persisted_secret
from config import app_config
from uzoncalc.cli_core.cli_workspace_archive import (
    WorkspaceArchive,
    read_workspace_archive,
    write_workspace_archive,
)
from uzoncalc.cli_core.cli_thumbnail import render_workspace_archive_thumbnail

_ARCHIVE_KIND = "uzoncalc.report-closure"


@dataclass(frozen=True)
class ExportedArchive:
    """Describe a temporary archive response owned by the controller.

    Attributes:
        path: Temporary PNG archive path.
        filename: Download filename presented to the client.
    """

    path: Path
    filename: str


async def export_version_closure(
    root_report: CalcReport,
    root_version: CalcReportVersion,
    *,
    can_edit: bool,
    can_share: bool,
    session: AsyncSession,
) -> ExportedArchive:
    """Build one portable archive from a published dependency closure.

    Args:
        root_report: Root report being exported.
        root_version: Immutable root version selected for export.
        can_edit: Application permission granted to archive importers.
        can_share: Application resharing permission granted to importers.
        session: Database session used to resolve the closure.

    Returns:
        Temporary archive path and safe download filename.

    Raises:
        CustomException: If the published closure is incomplete.
        OSError: If the temporary archive cannot be written.
    """
    closure = await _collect_shared_closure(root_report, root_version, session)
    files: dict[str, bytes] = {}
    report_nodes: list[dict] = []
    root_files: dict[str, bytes] | None = None
    root_files_prefix = ""
    root_entry_path = ""
    for node in closure:
        node_key = _archive_node_key(node)
        prefix = f"reports/{node_key}/"
        artifact_files = list(artifact_store.read_all(node.artifact.storageKey))
        workspace_files = {
            artifact_file.path: artifact_file.content
            for artifact_file in artifact_files
        }
        for artifact_file in artifact_files:
            files[f"{prefix}{artifact_file.path}"] = artifact_file.content
        if node.version.id == root_version.id:
            root_files = workspace_files
            root_files_prefix = prefix
            root_entry_path = node.artifact.manifest["calcbook"]["entryPath"]
        report_nodes.append(
            {
                "nodeKey": node_key,
                "reportKey": node.report.oid,
                "name": node.report.name,
                "description": node.report.description,
                "cover": node.report.cover,
                "versionName": _version_name(node.version),
                "versionDescription": node.version.description,
                "isRoot": node.version.id == root_version.id,
                "isLatest": node.version.id == node.report.latestVersionId,
                "filesPrefix": prefix,
                "calcbook": node.artifact.manifest["calcbook"],
                "dependencies": node.artifact.manifest.get("dependencies", []),
                "artifactHash": node.artifact.contentHash,
            }
        )
    if root_files is None:
        raise ValueError("导出闭包缺少根计算书")
    thumbnail_png, auto_view_entry = render_workspace_archive_thumbnail(
        root_files,
        root_entry_path,
        title=root_report.name,
        description=root_report.description,
    )
    manifest = {
        "kind": _ARCHIVE_KIND,
        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "rootNodeKey": _archive_node_key(
            next(node for node in closure if node.version.id == root_version.id)
        ),
        "permissions": {"canEdit": can_edit, "canShare": can_share},
        "executable": {
            "filesPrefix": root_files_prefix,
            "entryPath": root_entry_path,
            "autoViewEntry": auto_view_entry,
        },
        "reports": report_nodes,
    }
    temp_dir = Path(tempfile.mkdtemp(prefix="uzoncalc-export-"))
    archive_path = temp_dir / "report.png"
    try:
        write_workspace_archive(archive_path, thumbnail_png, manifest, files)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    filename = f"{_safe_filename(root_report.name)}-{_version_name(root_version)}.png"
    return ExportedArchive(path=archive_path, filename=filename)


async def import_archive_closure(
    user_id: int,
    request: ShareImportDTO,
    archive_bytes: bytes,
    session: AsyncSession,
    *,
    sync_locator: str | None = None,
) -> ShareImportResDTO:
    """Validate a v3 archive and reconstruct its complete owned closure.

    Args:
        user_id: Receiving user database identifier.
        request: Receiver category, root name, and synchronization preference.
        archive_bytes: Complete untrusted PNG or UZC container bytes.
        session: Database session used for atomic model creation.
        sync_locator: Optional encrypted upstream source URL for remote synchronization.

    Returns:
        Imported root identity, version, and closure count.

    Raises:
        CustomException: If the archive, category, graph, or permissions are invalid.
    """
    try:
        archive = read_workspace_archive(
            archive_bytes,
            max_file_count=app_config.calc_report_max_file_count,
            max_file_size=app_config.calc_report_max_file_size,
            max_total_size=app_config.calc_report_max_total_size,
        )
        nodes, root_node, permissions = _validate_manifest(archive)
    except ValueError as error:
        raise_ex(
            f"Invalid v3 report archive: {error}",
            code=400,
            error_code=CalcErrorCode.ARCHIVE_INVALID,
        )
    category = await session.scalar(
        select(CalcReportCategory).where(
            CalcReportCategory.oid == request.categoryOid,
            CalcReportCategory.userId == user_id,
            CalcReportCategory.deletedAt.is_(None),
        )
    )
    if category is None:
        raise_ex(
            "Category not found", code=404, error_code=CalcErrorCode.CATEGORY_NOT_FOUND
        )

    nodes_by_report: dict[str, list[dict]] = {}
    for node in nodes:
        nodes_by_report.setdefault(node["reportKey"], []).append(node)
    imported_reports: dict[str, CalcReport] = {}
    for report_key, report_nodes in nodes_by_report.items():
        descriptor = report_nodes[0]
        preferred_name = (
            request.name if report_key == root_node["reportKey"] else descriptor["name"]
        )
        imported = CalcReport(
            userId=user_id,
            categoryId=category.id,
            name=await _available_report_name(
                user_id, category.id, preferred_name or descriptor["name"], session
            ),
            description=descriptor.get("description"),
            cover=descriptor.get("cover"),
            workspaceRevision=1,
            originType=(
                ReportOriginType.SHARE_SYNC.value
                if request.shouldSync and report_key == root_node["reportKey"]
                else (
                    ReportOriginType.SHARE_IMPORT.value
                    if sync_locator
                    else ReportOriginType.FILE_IMPORT.value
                )
            ),
            canEdit=bool(permissions["canEdit"])
            and not (request.shouldSync and report_key == root_node["reportKey"]),
            canShare=bool(permissions["canShare"]),
            isSystemComponent=report_key != root_node["reportKey"],
        )
        session.add(imported)
        await session.flush()
        imported_reports[report_key] = imported

    imported_versions: dict[str, CalcReportVersion] = {}
    imported_artifacts: dict[str, CalcReportArtifact] = {}
    rewritten_dependencies: dict[str, list[dict]] = {}
    for node in nodes:
        dependencies = []
        for declaration in node["dependencies"]:
            target = imported_reports.get(declaration["targetReportOid"])
            if target is None:
                raise_ex("Archive dependency closure is incomplete", code=400)
            rewritten = dict(declaration)
            rewritten["targetReportOid"] = target.oid
            dependencies.append(rewritten)
        prefix = node["filesPrefix"]
        artifact_files = [
            ArtifactFile(path=path.removeprefix(prefix), content=content)
            for path, content in archive.files.items()
            if path.startswith(prefix)
        ]
        published = artifact_store.publish_source(
            artifact_files, node["calcbook"], dependencies
        )
        artifact = await _get_or_create_source_artifact(published, session)
        major, minor, patch = _parse_archive_version(node["versionName"])
        version = CalcReportVersion(
            reportId=imported_reports[node["reportKey"]].id,
            sourceArtifactId=artifact.id,
            major=major,
            minor=minor,
            patch=patch,
            description=node.get("versionDescription"),
            publishedByUserId=user_id,
        )
        session.add(version)
        await session.flush()
        imported_versions[node["nodeKey"]] = version
        imported_artifacts[node["nodeKey"]] = artifact
        rewritten_dependencies[node["nodeKey"]] = dependencies

    chosen_nodes: dict[str, dict] = {}
    for report_key, report_nodes in nodes_by_report.items():
        latest = next((node for node in report_nodes if node["isLatest"]), None)
        chosen_nodes[report_key] = (
            root_node
            if report_key == root_node["reportKey"]
            else latest or report_nodes[0]
        )
    for report_key, node in chosen_nodes.items():
        report = imported_reports[report_key]
        version = imported_versions[node["nodeKey"]]
        artifact = imported_artifacts[node["nodeKey"]]
        report.workspaceArtifactId = artifact.id
        report.latestVersionId = version.id
        report.entryPath = artifact.manifest["calcbook"]["entryPath"]
        report.formatVersion = artifact.manifest["calcbook"]["formatVersion"]
    await session.flush()

    for report_key, node in chosen_nodes.items():
        report = imported_reports[report_key]
        dependency_dtos = [
            ReportDependencyDTO.model_validate(value)
            for value in rewritten_dependencies[node["nodeKey"]]
        ]
        _, dependency_models = await _resolve_dependencies(
            user_id, report, report.oid, dependency_dtos, session
        )
        await _replace_dependencies(report.id, dependency_models, session)
        session.add(
            CalcReportOrigin(
                reportId=report.id,
                sourceArchiveHash=hashlib.sha256(archive_bytes).hexdigest(),
                sourceArtifactId=imported_artifacts[node["nodeKey"]].id,
                originMetadata={
                    "archiveFormat": "v3",
                    "sourceReportOid": report_key,
                    "sourceVersionName": node["versionName"],
                },
            )
        )
    imported_root = imported_reports[root_node["reportKey"]]
    if request.shouldSync and sync_locator:
        session.add(
            CalcReportSyncSource(
                reportId=imported_root.id,
                sourceLocator=encrypt_persisted_secret(f"remote:{sync_locator}"),
                sourceReportOid=root_node["reportKey"],
                sourceVersionName=root_node["versionName"],
                sourceArtifactHash=root_node["artifactHash"],
            )
        )
    await session.commit()
    for node in nodes:
        report = imported_reports[node["reportKey"]]
        _materialize_version_projection(
            user_id,
            report,
            imported_versions[node["nodeKey"]],
            imported_artifacts[node["nodeKey"]],
        )
    for report_key, node in chosen_nodes.items():
        report = imported_reports[report_key]
        version = imported_versions[node["nodeKey"]]
        artifact = imported_artifacts[node["nodeKey"]]
        _materialize_workspace_projection(user_id, report, artifact)
        write_latest_projection(user_id, report, version)
    return ShareImportResDTO(
        reportOid=imported_root.oid,
        versionName=root_node["versionName"],
        importedReportCount=len(imported_reports),
    )


async def synchronize_archive_closure(
    user_id: int,
    imported_root: CalcReport,
    sync_source: CalcReportSyncSource,
    archive_bytes: bytes,
    session: AsyncSession,
) -> str:
    """Atomically update an existing remote-synchronized archive closure.

    Args:
        user_id: Owner of the imported closure.
        imported_root: Stable local root report to update in place.
        sync_source: Persisted remote synchronization cursor.
        archive_bytes: Newly downloaded and bounded v3 archive.
        session: Database session used for staging and the final commit.

    Returns:
        Newly synchronized root semantic version.

    Raises:
        CustomException: If the archive identity, graph, or immutable versions conflict.
    """
    try:
        archive = read_workspace_archive(
            archive_bytes,
            max_file_count=app_config.calc_report_max_file_count,
            max_file_size=app_config.calc_report_max_file_size,
            max_total_size=app_config.calc_report_max_total_size,
        )
        nodes, root_node, permissions = _validate_manifest(archive)
    except ValueError as error:
        raise_ex(f"Invalid synchronized archive: {error}", code=400)
    if root_node["reportKey"] != sync_source.sourceReportOid:
        raise_ex("Synchronized source identity changed", code=409)

    origin_rows = (
        await session.execute(
            select(CalcReportOrigin, CalcReport)
            .join(CalcReport, CalcReport.id == CalcReportOrigin.reportId)
            .where(CalcReport.userId == user_id, CalcReport.deletedAt.is_(None))
        )
    ).all()
    imported_by_source_key: dict[str, CalcReport] = {}
    origin_by_source_key: dict[str, CalcReportOrigin] = {}
    for origin, report in origin_rows:
        metadata = origin.originMetadata or {}
        source_key = metadata.get("sourceReportOid")
        if isinstance(source_key, str):
            imported_by_source_key[source_key] = report
            origin_by_source_key[source_key] = origin
    imported_by_source_key[root_node["reportKey"]] = imported_root

    nodes_by_report: dict[str, list[dict]] = {}
    for node in nodes:
        nodes_by_report.setdefault(node["reportKey"], []).append(node)
    root_category = await session.get(CalcReportCategory, imported_root.categoryId)
    if root_category is None:
        raise_ex("Synchronized report category is unavailable", code=409)
    for report_key, report_nodes in nodes_by_report.items():
        if report_key in imported_by_source_key:
            continue
        descriptor = report_nodes[0]
        imported = CalcReport(
            userId=user_id,
            categoryId=root_category.id,
            name=await _available_report_name(
                user_id, root_category.id, descriptor["name"], session
            ),
            description=descriptor.get("description"),
            cover=descriptor.get("cover"),
            workspaceRevision=1,
            originType=ReportOriginType.SHARE_IMPORT.value,
            canEdit=False,
            canShare=bool(permissions["canShare"]),
            isSystemComponent=True,
        )
        session.add(imported)
        await session.flush()
        origin = CalcReportOrigin(
            reportId=imported.id,
            sourceArchiveHash=hashlib.sha256(archive_bytes).hexdigest(),
            originMetadata={"archiveFormat": "v3", "sourceReportOid": report_key},
        )
        session.add(origin)
        imported_by_source_key[report_key] = imported
        origin_by_source_key[report_key] = origin

    versions: dict[str, CalcReportVersion] = {}
    artifacts: dict[str, CalcReportArtifact] = {}
    dependencies_by_node: dict[str, list[dict]] = {}
    for node in nodes:
        rewritten_dependencies = []
        for declaration in node["dependencies"]:
            target = imported_by_source_key.get(declaration["targetReportOid"])
            if target is None:
                raise_ex("Synchronized dependency closure is incomplete", code=409)
            rewritten = dict(declaration)
            rewritten["targetReportOid"] = target.oid
            rewritten_dependencies.append(rewritten)
        prefix = node["filesPrefix"]
        published = artifact_store.publish_source(
            [
                ArtifactFile(path=path.removeprefix(prefix), content=content)
                for path, content in archive.files.items()
                if path.startswith(prefix)
            ],
            node["calcbook"],
            rewritten_dependencies,
        )
        artifact = await _get_or_create_source_artifact(published, session)
        report = imported_by_source_key[node["reportKey"]]
        major, minor, patch = _parse_archive_version(node["versionName"])
        version = await session.scalar(
            select(CalcReportVersion).where(
                CalcReportVersion.reportId == report.id,
                CalcReportVersion.major == major,
                CalcReportVersion.minor == minor,
                CalcReportVersion.patch == patch,
            )
        )
        if version is None:
            version = CalcReportVersion(
                reportId=report.id,
                sourceArtifactId=artifact.id,
                major=major,
                minor=minor,
                patch=patch,
                description=node.get("versionDescription"),
                publishedByUserId=user_id,
            )
            session.add(version)
            await session.flush()
        elif version.sourceArtifactId != artifact.id:
            raise_ex("Remote source changed an immutable semantic version", code=409)
        versions[node["nodeKey"]] = version
        artifacts[node["nodeKey"]] = artifact
        dependencies_by_node[node["nodeKey"]] = rewritten_dependencies

    chosen_nodes: dict[str, dict] = {}
    for report_key, report_nodes in nodes_by_report.items():
        latest = next((node for node in report_nodes if node["isLatest"]), None)
        chosen_nodes[report_key] = (
            root_node
            if report_key == root_node["reportKey"]
            else latest or report_nodes[0]
        )
    for report_key, node in chosen_nodes.items():
        report = imported_by_source_key[report_key]
        version = versions[node["nodeKey"]]
        artifact = artifacts[node["nodeKey"]]
        report.workspaceArtifactId = artifact.id
        report.latestVersionId = version.id
        report.entryPath = artifact.manifest["calcbook"]["entryPath"]
        report.formatVersion = artifact.manifest["calcbook"]["formatVersion"]
        report.canShare = bool(permissions["canShare"])
        dependency_dtos = [
            ReportDependencyDTO.model_validate(value)
            for value in dependencies_by_node[node["nodeKey"]]
        ]
        _, dependency_models = await _resolve_dependencies(
            user_id, report, report.oid, dependency_dtos, session
        )
        await _replace_dependencies(report.id, dependency_models, session)
        origin = origin_by_source_key.get(report_key)
        if origin is not None:
            origin.sourceArtifactId = artifact.id
            origin.sourceArchiveHash = hashlib.sha256(archive_bytes).hexdigest()
            origin.originMetadata = {
                "archiveFormat": "v3",
                "sourceReportOid": report_key,
                "sourceVersionName": node["versionName"],
            }
    now = datetime.datetime.now(datetime.timezone.utc)
    sync_source.sourceVersionName = root_node["versionName"]
    sync_source.sourceArtifactHash = root_node["artifactHash"]
    sync_source.lastCheckedAt = now
    sync_source.lastSyncedAt = now
    await session.commit()
    for node in nodes:
        _materialize_version_projection(
            user_id,
            imported_by_source_key[node["reportKey"]],
            versions[node["nodeKey"]],
            artifacts[node["nodeKey"]],
        )
    for report_key, node in chosen_nodes.items():
        report = imported_by_source_key[report_key]
        version = versions[node["nodeKey"]]
        artifact = artifacts[node["nodeKey"]]
        _materialize_workspace_projection(user_id, report, artifact)
        write_latest_projection(user_id, report, version)
    return root_node["versionName"]


def inspect_archive_root(archive_bytes: bytes) -> tuple[str, str, str]:
    """Return portable root identity, version, and source artifact hash.

    Args:
        archive_bytes: Complete bounded v3 archive bytes.

    Returns:
        Source report key, semantic version, and original artifact hash.

    Raises:
        ValueError: If the core archive or report manifest is invalid.
    """
    archive = read_workspace_archive(
        archive_bytes,
        max_file_count=app_config.calc_report_max_file_count,
        max_file_size=app_config.calc_report_max_file_size,
        max_total_size=app_config.calc_report_max_total_size,
    )
    _nodes, root_node, _permissions = _validate_manifest(archive)
    return (
        root_node["reportKey"],
        root_node["versionName"],
        root_node["artifactHash"],
    )


def remove_exported_archive(exported: ExportedArchive) -> None:
    """Remove an exported archive and its dedicated temporary directory.

    Args:
        exported: Completed export returned by :func:`export_version_closure`.

    Returns:
        None.
    """
    shutil.rmtree(exported.path.parent, ignore_errors=True)


def _validate_manifest(
    archive: WorkspaceArchive,
) -> tuple[list[dict], dict, dict[str, bool]]:
    """Validate the report-specific structure layered over the core manifest."""
    manifest = archive.manifest
    if manifest.get("kind") != _ARCHIVE_KIND:
        raise ValueError("归档类型不受支持")
    nodes = manifest.get("reports")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("归档报告清单为空")
    root_node_key = manifest.get("rootNodeKey")
    permissions = manifest.get("permissions")
    if not isinstance(permissions, dict) or not all(
        isinstance(permissions.get(key), bool) for key in ("canEdit", "canShare")
    ):
        raise ValueError("归档权限声明无效")
    executable = manifest.get("executable")
    if (
        not isinstance(executable, dict)
        or not isinstance(executable.get("filesPrefix"), str)
        or not isinstance(executable.get("entryPath"), str)
        or (
            executable.get("autoViewEntry") is not None
            and not isinstance(executable.get("autoViewEntry"), str)
        )
    ):
        raise ValueError("归档可执行入口声明无效")
    node_keys: set[str] = set()
    versions_by_report: set[tuple[str, str]] = set()
    prefixes: set[str] = set()
    required = {
        "nodeKey": str,
        "reportKey": str,
        "name": str,
        "versionName": str,
        "filesPrefix": str,
        "calcbook": dict,
        "dependencies": list,
        "artifactHash": str,
        "isRoot": bool,
        "isLatest": bool,
    }
    for node in nodes:
        if not isinstance(node, dict) or any(
            not isinstance(node.get(key), value_type)
            for key, value_type in required.items()
        ):
            raise ValueError("归档报告节点无效")
        _parse_archive_version(node["versionName"])
        identity = (node["reportKey"], node["versionName"])
        if node["nodeKey"] in node_keys or identity in versions_by_report:
            raise ValueError("归档报告节点重复")
        prefix = node["filesPrefix"]
        if not prefix.endswith("/") or prefix in prefixes:
            raise ValueError("归档报告文件前缀无效")
        matching_paths = [path for path in archive.files if path.startswith(prefix)]
        if not matching_paths or f"{prefix}calcbook.json" not in matching_paths:
            raise ValueError("归档报告文件不完整")
        for declaration in node["dependencies"]:
            if not isinstance(declaration, dict) or not isinstance(
                declaration.get("targetReportOid"), str
            ):
                raise ValueError("归档依赖声明无效")
        node_keys.add(node["nodeKey"])
        versions_by_report.add(identity)
        prefixes.add(prefix)
    roots = [node for node in nodes if node["isRoot"]]
    if len(roots) != 1 or roots[0]["nodeKey"] != root_node_key:
        raise ValueError("归档根报告声明无效")
    if executable["filesPrefix"] != roots[0]["filesPrefix"] or executable[
        "entryPath"
    ] != roots[0]["calcbook"].get("entryPath"):
        raise ValueError("归档可执行入口与根报告不一致")
    report_keys = {node["reportKey"] for node in nodes}
    if any(
        declaration["targetReportOid"] not in report_keys
        for node in nodes
        for declaration in node["dependencies"]
    ):
        raise ValueError("归档依赖闭包不完整")
    return cast(list[dict], nodes), roots[0], cast(dict[str, bool], permissions)


def _archive_node_key(node: SharedVersionNode) -> str:
    """Return one portable node key without path-unsafe separators."""
    return f"{node.report.oid}-{_version_name(node.version).replace('.', '_')}"


def _version_name(version: CalcReportVersion) -> str:
    """Format one immutable semantic version."""
    return f"{version.major}.{version.minor}.{version.patch}"


def _parse_archive_version(version_name: str) -> tuple[int, int, int]:
    """Parse a strict non-negative three-part semantic version."""
    parts = version_name.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError("归档版本号无效")
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def _safe_filename(value: str) -> str:
    """Return a conservative cross-platform archive filename stem."""
    sanitized = "".join(
        character if character.isalnum() else "-" for character in value
    )
    return sanitized.strip("-")[:60] or "report"
