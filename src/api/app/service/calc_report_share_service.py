"""Published-version share links and full dependency-closure imports."""

from __future__ import annotations

import datetime
import hashlib
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_execution_dto import (
    CalcExecutionSourceDTO,
    CalcExecutionStartDTO,
)
from app.controller.calc.calc_state import (
    ReservedDependencySelectorKey,
    ReportSyncState,
    ExecutionSourceType as PublicExecutionSourceType,
    ShareAccessType,
)
from app.controller.calc.calc_share_dto import (
    ShareImportDTO,
    ShareImportResDTO,
    ReportSyncResDTO,
    ShareCatalogFilterDTO,
    ShareLinkCreateDTO,
    ShareLinkResDTO,
    SharePreviewResDTO,
    SharedReportResDTO,
    ShareDepartmentOptionDTO,
    ShareUserOptionDTO,
)
from app.controller.dto_base import PaginationDTO
from app.controller.calc.calc_workspace_dto import ReportDependencyDTO
from app.db.models.calc_report import (
    CalcReport,
    CalcReportOrigin,
    CalcReportSyncSource,
)
from app.db.models.calc_report_artifact import CalcReportArtifact
from app.db.models.calc_report_category import CalcReportCategory
from app.db.models.calc_report_share import (
    CalcReportShareDepartment,
    CalcReportShareLink,
    CalcReportShareRecipient,
)
from app.db.models.department import Department, DepartmentUser
from app.db.models.calc_report_version import CalcReportVersion
from app.db.models.calc_execution import CalcExecution
from app.db.models.enums import (
    ArtifactKind,
    ReportOriginType,
    ShareAccessType as DbShareAccessType,
)
from app.db.models.object_id import ObjectId
from app.db.models.user import User, UserStatus
from app.exception.custom_exception import CustomException, raise_ex
from app.i18n import _
from app.service.calc_report_artifact_service import artifact_store
from app.service.calc_report_workspace_service import (
    _get_or_create_source_artifact,
    _materialize_workspace_projection,
    _replace_dependencies,
    _resolve_dependencies,
    parse_version_name,
)
from app.service.calc_report_service import write_latest_projection
from app.service.calc_report_version_service import _materialize_version_projection
from app.service.calc_execution_service import (
    ExecutionStep,
    get_execution_step,
    start_execution,
)
from app.service.department_service import descendant_department_ids
from app.service.secret_storage_service import (
    decrypt_persisted_secret,
    encrypt_persisted_secret,
)


@dataclass(frozen=True)
class SharedVersionNode:
    """Hold one published report/version/artifact node in an import closure."""

    report: CalcReport
    version: CalcReportVersion
    artifact: CalcReportArtifact


async def create_share_link(
    user_id: int,
    report_oid: str,
    request: ShareLinkCreateDTO,
    session: AsyncSession,
) -> ShareLinkResDTO:
    """Create a secret link for a published version and return its token once."""
    report = await _get_owned_report(user_id, report_oid, session)
    if not report.canShare:
        raise_ex(
            "Report sharing is not permitted",
            code=403,
            error_code=CalcErrorCode.SHARE_NOT_ALLOWED,
        )
    version = await _get_version(report, request.versionName, session)
    await _collect_shared_closure(report, version, session)
    recipients = await _resolve_recipients(request.recipientUserOids, session)
    departments = await _resolve_departments(request.recipientDepartmentOids, session)
    token = secrets.token_urlsafe(32)
    access_type = DbShareAccessType[request.accessType.name]
    link = CalcReportShareLink(
        reportId=report.id,
        versionId=version.id,
        tokenHash=_token_hash(token),
        accessType=access_type.value,
        expiresAt=request.expiresAt,
        maxUseCount=request.maxUseCount,
        canEdit=request.canEdit,
        canShare=request.canShare,
        note=request.note.strip() if request.note and request.note.strip() else None,
        createdByUserId=user_id,
    )
    session.add(link)
    await session.flush()
    for recipient in recipients:
        session.add(CalcReportShareRecipient(shareLinkId=link.id, userId=recipient.id))
    for department in departments:
        session.add(
            CalcReportShareDepartment(shareLinkId=link.id, departmentId=department.id)
        )
    await session.commit()
    await session.refresh(link)
    return _share_link_response(
        link,
        report,
        version,
        token=token,
        recipient_user_oids=[recipient.oid for recipient in recipients],
        recipient_department_oids=[department.oid for department in departments],
    )


async def list_share_links(
    user_id: int, report_oid: str, session: AsyncSession
) -> list[ShareLinkResDTO]:
    """List share metadata created by the current owner for one report."""
    report = await _get_owned_report(user_id, report_oid, session)
    rows = (
        await session.execute(
            select(CalcReportShareLink, CalcReportVersion)
            .join(
                CalcReportVersion, CalcReportVersion.id == CalcReportShareLink.versionId
            )
            .where(CalcReportVersion.reportId == report.id)
            .order_by(CalcReportShareLink.createdAt.desc())
        )
    ).all()
    responses = []
    for link, version in rows:
        recipient_user_oids, recipient_department_oids = await _share_recipient_oids(
            link.id, session
        )
        responses.append(
            _share_link_response(
                link,
                report,
                version,
                recipient_user_oids=recipient_user_oids,
                recipient_department_oids=recipient_department_oids,
            )
        )
    return responses


async def update_share_link(
    user_id: int,
    share_oid: str,
    request: ShareLinkCreateDTO,
    session: AsyncSession,
) -> ShareLinkResDTO:
    """Replace the editable settings of one active owned share link.

    Args:
        user_id: Current owner database identifier.
        share_oid: Public share-link identifier.
        request: Complete replacement settings.
        session: Active database session.

    Returns:
        Updated link metadata without exposing its bearer token.

    Raises:
        CustomException: If ownership, version, recipients, or link state is invalid.
    """
    link, report, _current_version = await _get_owned_share(user_id, share_oid, session)
    if link.revokedAt is not None:
        raise_ex(_("A revoked share link cannot be edited"), code=409)
    version = await _get_version(report, request.versionName, session)
    await _collect_shared_closure(report, version, session)
    recipients = await _resolve_recipients(request.recipientUserOids, session)
    departments = await _resolve_departments(request.recipientDepartmentOids, session)
    link.versionId = version.id
    link.accessType = DbShareAccessType[request.accessType.name].value
    link.expiresAt = request.expiresAt
    link.maxUseCount = request.maxUseCount
    link.canEdit = request.canEdit
    link.canShare = request.canShare
    link.note = request.note.strip() if request.note and request.note.strip() else None
    link.previewExecutionId = None
    await session.execute(
        delete(CalcReportShareRecipient).where(
            CalcReportShareRecipient.shareLinkId == link.id
        )
    )
    await session.execute(
        delete(CalcReportShareDepartment).where(
            CalcReportShareDepartment.shareLinkId == link.id
        )
    )
    session.add_all(
        [
            CalcReportShareRecipient(shareLinkId=link.id, userId=recipient.id)
            for recipient in recipients
        ]
        + [
            CalcReportShareDepartment(shareLinkId=link.id, departmentId=department.id)
            for department in departments
        ]
    )
    await session.commit()
    return _share_link_response(
        link,
        report,
        version,
        recipient_user_oids=[recipient.oid for recipient in recipients],
        recipient_department_oids=[department.oid for department in departments],
    )


async def revoke_share_link(
    user_id: int, share_oid: str, session: AsyncSession
) -> ShareLinkResDTO:
    """Revoke an owned share link idempotently."""
    link, report, version = await _get_owned_share(user_id, share_oid, session)
    if link.revokedAt is None:
        link.revokedAt = datetime.datetime.now(datetime.timezone.utc)
        await session.commit()
    return _share_link_response(link, report, version)


async def preview_share(
    user_id: int | None, token: str, session: AsyncSession
) -> SharePreviewResDTO:
    """Validate share authorization and return its full published footprint."""
    link, report, version = await _authorize_share(user_id, token, session)
    closure = await _collect_shared_closure(report, version, session)
    return SharePreviewResDTO(
        reportName=report.name,
        reportDescription=report.description,
        reportOid=report.oid,
        versionName=_version_name(version),
        dependencyCount=max(0, len(closure) - 1),
        totalFileCount=sum(node.artifact.fileCount for node in closure),
        totalSize=sum(node.artifact.totalSize for node in closure),
        canEdit=link.canEdit,
        canShare=link.canShare,
        note=link.note,
    )


async def get_or_run_share_preview(
    user_id: int | None, token: str, session: AsyncSession
) -> tuple[CalcReportShareLink, ExecutionStep]:
    """Return the share-specific recent run or execute true defaults once."""
    link, report, version = await _authorize_share(user_id, token, session)
    if link.previewExecutionId is not None:
        execution = await session.get(CalcExecution, link.previewExecutionId)
        if execution is not None and execution.resultPath:
            return link, await get_execution_step(
                session, link.createdByUserId, execution.oid
            )
    step = await start_execution(
        session,
        link.createdByUserId,
        CalcExecutionStartDTO(
            reportOid=report.oid,
            source=CalcExecutionSourceDTO(
                type=PublicExecutionSourceType.VERSION,
                versionName=_version_name(version),
            ),
            defaults={},
            isSilent=True,
        ),
        use_cached_defaults=False,
        persist_input_cache=False,
    )
    return link, step


async def record_share_preview_execution(
    link: CalcReportShareLink,
    execution: CalcExecution,
    session: AsyncSession,
) -> None:
    """Attach one finalized default execution to its share record."""
    link.previewExecutionId = execution.id
    await session.commit()


async def get_share_preview_result_path(
    user_id: int | None, token: str, session: AsyncSession
) -> Path:
    """Resolve share-specific HTML only after revalidating current access."""
    link, _, _ = await _authorize_share(user_id, token, session)
    execution = (
        await session.get(CalcExecution, link.previewExecutionId)
        if link.previewExecutionId is not None
        else None
    )
    if execution is None or not execution.resultPath:
        raise_ex("Shared report result is unavailable", code=404)
    relative_path = Path(execution.resultPath)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise_ex("Shared report result path is invalid", code=500)
    result_file = Path("data") / relative_path
    if not result_file.is_file():
        raise_ex("Shared report result is unavailable", code=404)
    return result_file


async def count_available_shares(
    user_id: int,
    filters: ShareCatalogFilterDTO,
    session: AsyncSession,
) -> int:
    """Count active same-backend shares available to the current user."""
    return len(await _available_shared_rows(user_id, filters, session))


async def list_share_user_options(
    query: str | None, session: AsyncSession
) -> list[ShareUserOptionDTO]:
    """List at most fifty active users matching a recipient search."""
    conditions = [User.status == UserStatus.Active.value]
    if query:
        pattern = f"%{query.strip()}%"
        conditions.append(
            or_(User.username.ilike(pattern), User.nickName.ilike(pattern))
        )
    users = (
        await session.scalars(
            select(User).where(*conditions).order_by(User.username).limit(50)
        )
    ).all()
    return [
        ShareUserOptionDTO(
            userOid=user.oid, username=user.username, nickName=user.nickName
        )
        for user in users
    ]


async def list_share_department_options(
    session: AsyncSession,
) -> list[ShareDepartmentOptionDTO]:
    """List active departments as flat parent-linked share options."""
    departments = (
        await session.scalars(
            select(Department)
            .where(Department.deletedAt.is_(None))
            .order_by(Department.parentId, Department.sortOrder, Department.id)
        )
    ).all()
    oid_by_id = {department.id: department.oid for department in departments}
    return [
        ShareDepartmentOptionDTO(
            departmentOid=department.oid,
            parentOid=oid_by_id.get(department.parentId),
            name=department.name,
        )
        for department in departments
    ]


async def list_available_shares(
    user_id: int,
    filters: ShareCatalogFilterDTO,
    pagination: PaginationDTO,
    session: AsyncSession,
) -> list[SharedReportResDTO]:
    """List one stable page from the current user's accessible share catalog."""
    rows = await _available_shared_rows(user_id, filters, session)
    sort_keys = {
        "reportName": lambda row: row[1].name.casefold(),
        "versionName": lambda row: (
            row[2].major,
            row[2].minor,
            row[2].patch,
        ),
        "sharedAt": lambda row: row[0].createdAt,
    }
    sort_key = sort_keys.get(pagination.sortBy, sort_keys["sharedAt"])
    rows.sort(key=sort_key, reverse=pagination.descending)
    page = rows[pagination.skip : pagination.skip + pagination.limit]
    return [
        SharedReportResDTO(
            shareOid=link.oid,
            reportName=report.name,
            qualifiedName=(
                f"{owner.nickName or owner.username}/{category.name}/{report.name}"
            ),
            sharedBy=owner.nickName or owner.username,
            description=report.description,
            note=link.note,
            versionName=_version_name(version),
            sharedAt=link.createdAt,
            canEdit=link.canEdit,
            canShare=link.canShare,
        )
        for link, report, version, owner, category in page
    ]


async def _available_shared_rows(
    user_id: int,
    filters: ShareCatalogFilterDTO,
    session: AsyncSession,
) -> list[
    tuple[CalcReportShareLink, CalcReport, CalcReportVersion, User, CalcReportCategory]
]:
    """Load and audience-filter active share catalog rows."""
    conditions = [
        CalcReportShareLink.revokedAt.is_(None),
        CalcReport.deletedAt.is_(None),
        User.status == UserStatus.Active.value,
    ]
    if filters.query:
        pattern = f"%{filters.query.strip()}%"
        conditions.append(
            or_(
                CalcReport.name.ilike(pattern),
                CalcReport.description.ilike(pattern),
                User.nickName.ilike(pattern),
                User.username.ilike(pattern),
                CalcReportCategory.name.ilike(pattern),
            )
        )
    candidates = (
        await session.execute(
            select(
                CalcReportShareLink,
                CalcReport,
                CalcReportVersion,
                User,
                CalcReportCategory,
            )
            .join(CalcReport, CalcReport.id == CalcReportShareLink.reportId)
            .join(
                CalcReportVersion, CalcReportVersion.id == CalcReportShareLink.versionId
            )
            .join(User, User.id == CalcReport.userId)
            .join(CalcReportCategory, CalcReportCategory.id == CalcReport.categoryId)
            .where(*conditions)
        )
    ).all()
    available = []
    for row in candidates:
        try:
            await _authorize_share_link(user_id, row[0], session)
        except CustomException:
            continue
        available.append(row)
    return available


async def get_report_sync_status(
    user_id: int, report_oid: str, session: AsyncSession
) -> ReportSyncResDTO:
    """Check whether a synchronized report has a newer upstream version."""
    report, sync_source = await _get_owned_sync_source(user_id, report_oid, session)
    locator = decrypt_persisted_secret(sync_source.sourceLocator)
    if locator.startswith("remote:"):
        try:
            (
                _archive_bytes,
                source_report_oid,
                upstream_version_name,
                artifact_hash,
            ) = await _get_remote_sync_snapshot(locator.removeprefix("remote:"))
            if source_report_oid != sync_source.sourceReportOid:
                raise ValueError("remote source identity changed")
            state = (
                ReportSyncState.CURRENT
                if artifact_hash == sync_source.sourceArtifactHash
                else ReportSyncState.UPDATE_AVAILABLE
            )
        except (CustomException, ValueError):
            state = ReportSyncState.SOURCE_UNAVAILABLE
            upstream_version_name = None
        sync_source.lastCheckedAt = datetime.datetime.now(datetime.timezone.utc)
        await session.commit()
        return ReportSyncResDTO(
            reportOid=report.oid,
            state=state,
            currentVersionName=sync_source.sourceVersionName,
            upstreamVersionName=upstream_version_name,
        )
    try:
        _, _, upstream_version = await _resolve_sync_upstream(
            user_id, sync_source, session
        )
        upstream_artifact = await session.get(
            CalcReportArtifact, upstream_version.sourceArtifactId
        )
        if upstream_artifact is None:
            raise_ex("Upstream source artifact is unavailable", code=404)
        state = (
            ReportSyncState.CURRENT
            if upstream_artifact.contentHash == sync_source.sourceArtifactHash
            else ReportSyncState.UPDATE_AVAILABLE
        )
        upstream_version_name = _version_name(upstream_version)
    except CustomException as error:
        state = (
            ReportSyncState.ACCESS_REVOKED
            if error.code in {401, 403, 404, 409}
            else ReportSyncState.SOURCE_UNAVAILABLE
        )
        upstream_version_name = None
    except ValueError:
        state = ReportSyncState.SOURCE_UNAVAILABLE
        upstream_version_name = None
    sync_source.lastCheckedAt = datetime.datetime.now(datetime.timezone.utc)
    await session.commit()
    return ReportSyncResDTO(
        reportOid=report.oid,
        state=state,
        currentVersionName=sync_source.sourceVersionName,
        upstreamVersionName=upstream_version_name,
    )


async def synchronize_report(
    user_id: int, report_oid: str, session: AsyncSession
) -> ReportSyncResDTO:
    """Atomically replace a synchronized report closure with upstream latest."""
    report, sync_source = await _get_owned_sync_source(user_id, report_oid, session)
    locator = decrypt_persisted_secret(sync_source.sourceLocator)
    if locator.startswith("remote:"):
        from app.service import calc_report_archive_service

        (
            archive_bytes,
            source_report_oid,
            upstream_version_name,
            artifact_hash,
        ) = await _get_remote_sync_snapshot(locator.removeprefix("remote:"))
        if source_report_oid != sync_source.sourceReportOid:
            raise_ex("Synchronized source identity changed", code=409)
        if artifact_hash != sync_source.sourceArtifactHash:
            upstream_version_name = (
                await calc_report_archive_service.synchronize_archive_closure(
                    user_id, report, sync_source, archive_bytes, session
                )
            )
        else:
            sync_source.lastCheckedAt = datetime.datetime.now(datetime.timezone.utc)
            await session.commit()
        return ReportSyncResDTO(
            reportOid=report.oid,
            state=ReportSyncState.CURRENT,
            currentVersionName=upstream_version_name,
            upstreamVersionName=upstream_version_name,
        )
    _, source_report, upstream_version = await _resolve_sync_upstream(
        user_id, sync_source, session
    )
    upstream_artifact = await session.get(
        CalcReportArtifact, upstream_version.sourceArtifactId
    )
    if upstream_artifact is None:
        raise_ex("Upstream source artifact is unavailable", code=404)
    if upstream_artifact.contentHash != sync_source.sourceArtifactHash:
        closure = await _collect_shared_closure(
            source_report, upstream_version, session
        )
        await _apply_sync_closure(
            user_id,
            report,
            sync_source,
            source_report,
            upstream_version,
            closure,
            session,
        )
    else:
        sync_source.lastCheckedAt = datetime.datetime.now(datetime.timezone.utc)
        await session.commit()
    return ReportSyncResDTO(
        reportOid=report.oid,
        state=ReportSyncState.CURRENT,
        currentVersionName=_version_name(upstream_version),
        upstreamVersionName=_version_name(upstream_version),
    )


async def _get_remote_sync_snapshot(
    source: str,
) -> tuple[bytes, str, str, str]:
    """Download and inspect one remote public synchronization archive.

    Args:
        source: Canonical remote public preview URL.

    Returns:
        Archive bytes, source report OID, root version, and source artifact hash.

    Raises:
        CustomException: If network validation or download fails.
        ValueError: If the v3 archive manifest is invalid.
    """
    from app.service import calc_report_archive_service, remote_share_service

    (
        archive_bytes,
        _canonical_source,
    ) = await remote_share_service.fetch_remote_share_archive(source)
    report_oid, version_name, artifact_hash = (
        calc_report_archive_service.inspect_archive_root(archive_bytes)
    )
    return archive_bytes, report_oid, version_name, artifact_hash


async def _get_owned_sync_source(
    user_id: int, report_oid: str, session: AsyncSession
) -> tuple[CalcReport, CalcReportSyncSource]:
    """Load one owned synchronized report and its encrypted source record."""
    row = (
        await session.execute(
            select(CalcReport, CalcReportSyncSource)
            .join(CalcReportSyncSource, CalcReportSyncSource.reportId == CalcReport.id)
            .where(
                CalcReport.oid == report_oid,
                CalcReport.userId == user_id,
                CalcReport.deletedAt.is_(None),
                CalcReport.originType == ReportOriginType.SHARE_SYNC.value,
            )
        )
    ).one_or_none()
    if row is None:
        raise_ex("Synchronized report not found", code=404)
    return row


async def _resolve_sync_upstream(
    user_id: int,
    sync_source: CalcReportSyncSource,
    session: AsyncSession,
) -> tuple[CalcReportShareLink, CalcReport, CalcReportVersion]:
    """Authorize the encrypted locator and resolve the upstream latest version."""
    locator = decrypt_persisted_secret(sync_source.sourceLocator)
    if locator.startswith("catalog:"):
        link = await session.scalar(
            select(CalcReportShareLink).where(
                CalcReportShareLink.oid == locator.removeprefix("catalog:")
            )
        )
        if link is None:
            raise_ex("Share link is unavailable", code=404)
        link, source_report, shared_version = await _authorize_share_link(
            user_id, link, session
        )
    else:
        link, source_report, shared_version = await _authorize_share(
            user_id, locator, session
        )
    if source_report.oid != sync_source.sourceReportOid:
        raise_ex("Synchronized source identity changed", code=409)
    upstream_version = (
        await session.get(CalcReportVersion, source_report.latestVersionId)
        if source_report.latestVersionId is not None
        else shared_version
    )
    if upstream_version is None:
        raise_ex("Upstream version is unavailable", code=404)
    return link, source_report, upstream_version


async def _apply_sync_closure(
    user_id: int,
    imported_root: CalcReport,
    sync_source: CalcReportSyncSource,
    source_root: CalcReport,
    source_root_version: CalcReportVersion,
    closure: list[SharedVersionNode],
    session: AsyncSession,
) -> None:
    """Stage a complete validated closure and atomically switch local latest pointers."""
    source_report_ids = {node.report.id for node in closure}
    imported_rows = (
        await session.execute(
            select(CalcReportOrigin, CalcReport)
            .join(CalcReport, CalcReport.id == CalcReportOrigin.reportId)
            .where(
                CalcReport.userId == user_id,
                CalcReport.deletedAt.is_(None),
                CalcReportOrigin.sourceReportId.in_(source_report_ids),
            )
        )
    ).all()
    imported_by_source_id = {
        origin.sourceReportId: report for origin, report in imported_rows
    }
    imported_by_source_id[source_root.id] = imported_root
    if source_report_ids - imported_by_source_id.keys():
        raise_ex("Synchronized dependency closure is incomplete", code=409)

    source_by_oid = {node.report.oid: node.report for node in closure}
    versions_by_source_version_id: dict[int, CalcReportVersion] = {}
    artifacts_by_source_version_id: dict[int, CalcReportArtifact] = {}
    dependencies_by_source_version_id: dict[int, list[dict]] = {}
    for node in reversed(closure):
        imported_report = imported_by_source_id[node.report.id]
        rewritten_dependencies = []
        for declaration in node.artifact.manifest.get("dependencies", []):
            target_source = source_by_oid.get(declaration["targetReportOid"])
            if target_source is None:
                raise_ex("Synchronized dependency target is missing", code=409)
            rewritten = dict(declaration)
            rewritten["targetReportOid"] = imported_by_source_id[target_source.id].oid
            rewritten_dependencies.append(rewritten)
        published = artifact_store.publish_source(
            artifact_store.read_all(node.artifact.storageKey),
            node.artifact.manifest["calcbook"],
            rewritten_dependencies,
        )
        artifact = await _get_or_create_source_artifact(published, session)
        version = await session.scalar(
            select(CalcReportVersion).where(
                CalcReportVersion.reportId == imported_report.id,
                CalcReportVersion.major == node.version.major,
                CalcReportVersion.minor == node.version.minor,
                CalcReportVersion.patch == node.version.patch,
            )
        )
        if version is None:
            version = CalcReportVersion(
                reportId=imported_report.id,
                sourceArtifactId=artifact.id,
                major=node.version.major,
                minor=node.version.minor,
                patch=node.version.patch,
                description=node.version.description,
                publishedByUserId=user_id,
            )
            session.add(version)
            await session.flush()
        elif version.sourceArtifactId != artifact.id:
            raise_ex("Upstream changed an immutable semantic version", code=409)
        versions_by_source_version_id[node.version.id] = version
        artifacts_by_source_version_id[node.version.id] = artifact
        dependencies_by_source_version_id[node.version.id] = rewritten_dependencies

    chosen_by_source_report_id: dict[int, SharedVersionNode] = {}
    for node in closure:
        chosen = chosen_by_source_report_id.get(node.report.id)
        if chosen is None or node.version.id == node.report.latestVersionId:
            chosen_by_source_report_id[node.report.id] = node
    chosen_by_source_report_id[source_root.id] = next(
        node for node in closure if node.version.id == source_root_version.id
    )
    for source_report_id, node in chosen_by_source_report_id.items():
        imported_report = imported_by_source_id[source_report_id]
        version = versions_by_source_version_id[node.version.id]
        artifact = artifacts_by_source_version_id[node.version.id]
        imported_report.workspaceArtifactId = artifact.id
        imported_report.latestVersionId = version.id
        imported_report.entryPath = artifact.manifest["calcbook"]["entryPath"]
        imported_report.formatVersion = artifact.manifest["calcbook"]["formatVersion"]
        dependency_dtos = [
            ReportDependencyDTO.model_validate(value)
            for value in dependencies_by_source_version_id[node.version.id]
        ]
        _, dependency_models = await _resolve_dependencies(
            user_id, imported_report, imported_report.oid, dependency_dtos, session
        )
        await _replace_dependencies(imported_report.id, dependency_models, session)
        origin = next(
            (
                origin
                for origin, report in imported_rows
                if report.id == imported_report.id
            ),
            None,
        )
        if origin is not None:
            origin.sourceVersionId = node.version.id
            origin.sourceArtifactId = node.artifact.id

    root_artifact = artifacts_by_source_version_id[source_root_version.id]
    sync_source.sourceVersionName = _version_name(source_root_version)
    sync_source.sourceArtifactHash = root_artifact.contentHash
    sync_source.lastCheckedAt = datetime.datetime.now(datetime.timezone.utc)
    sync_source.lastSyncedAt = datetime.datetime.now(datetime.timezone.utc)
    await session.commit()
    for node in closure:
        _materialize_version_projection(
            user_id,
            imported_by_source_id[node.report.id],
            versions_by_source_version_id[node.version.id],
            artifacts_by_source_version_id[node.version.id],
        )
    for source_report_id, node in chosen_by_source_report_id.items():
        imported_report = imported_by_source_id[source_report_id]
        version = versions_by_source_version_id[node.version.id]
        artifact = artifacts_by_source_version_id[node.version.id]
        _materialize_workspace_projection(user_id, imported_report, artifact)
        write_latest_projection(user_id, imported_report, version)


async def import_share(
    user_id: int,
    token: str,
    request: ShareImportDTO,
    session: AsyncSession,
) -> ShareImportResDTO:
    """Import a full published closure as receiver-owned reports and versions."""
    link, root_report, root_version = await _authorize_share(user_id, token, session)
    return await _import_share_models(
        user_id,
        link,
        root_report,
        root_version,
        request,
        session,
        sync_locator=token,
    )


async def import_catalog_share(
    user_id: int,
    share_oid: str,
    request: ShareImportDTO,
    session: AsyncSession,
) -> ShareImportResDTO:
    """Import one accessible same-backend catalog share without its bearer token."""
    link = await session.scalar(
        select(CalcReportShareLink).where(CalcReportShareLink.oid == share_oid)
    )
    if link is None:
        raise_ex("Share link is unavailable", code=404)
    link, report, version = await _authorize_share_link(user_id, link, session)
    return await _import_share_models(
        user_id,
        link,
        report,
        version,
        request,
        session,
        sync_locator=f"catalog:{share_oid}",
    )


async def _import_share_models(
    user_id: int,
    link: CalcReportShareLink,
    root_report: CalcReport,
    root_version: CalcReportVersion,
    request: ShareImportDTO,
    session: AsyncSession,
    *,
    sync_locator: str | None,
) -> ShareImportResDTO:
    """Import a validated dependency closure into receiver-owned models."""
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
    closure = await _collect_shared_closure(root_report, root_version, session)
    await _consume_share(link, session)

    nodes_by_report: dict[int, list[SharedVersionNode]] = {}
    for node in closure:
        nodes_by_report.setdefault(node.report.id, []).append(node)

    imported_reports: dict[int, CalcReport] = {}
    for node in reversed(closure):
        if node.report.id in imported_reports:
            continue
        requested_name = (
            request.name if node.report.id == root_report.id else node.report.name
        )
        unique_name = await _available_report_name(
            user_id, category.id, requested_name or node.report.name, session
        )
        imported = CalcReport(
            userId=user_id,
            categoryId=category.id,
            name=unique_name,
            description=node.report.description,
            cover=node.report.cover,
            entryPath=node.report.entryPath,
            formatVersion=node.report.formatVersion,
            workspaceRevision=1,
            originType=(
                ReportOriginType.SHARE_SYNC.value
                if request.shouldSync and node.report.id == root_report.id
                else ReportOriginType.SHARE_IMPORT.value
            ),
            canEdit=link.canEdit and not request.shouldSync,
            canShare=link.canShare,
            isSystemComponent=node.report.id != root_report.id,
        )
        session.add(imported)
        await session.flush()
        imported_reports[node.report.id] = imported

    imported_versions: dict[int, CalcReportVersion] = {}
    imported_artifacts: dict[int, CalcReportArtifact] = {}
    rewritten_dependencies_by_version: dict[int, list[dict]] = {}
    for node in reversed(closure):
        imported = imported_reports[node.report.id]
        rewritten_dependencies = []
        for declaration in node.artifact.manifest.get("dependencies", []):
            original_target = await session.scalar(
                select(CalcReport).where(
                    CalcReport.oid == declaration["targetReportOid"]
                )
            )
            if original_target is None or original_target.id not in imported_reports:
                raise_ex("Shared dependency closure is incomplete", code=500)
            rewritten = dict(declaration)
            rewritten["targetReportOid"] = imported_reports[original_target.id].oid
            rewritten_dependencies.append(rewritten)
        published = artifact_store.publish_source(
            artifact_store.read_all(node.artifact.storageKey),
            node.artifact.manifest["calcbook"],
            rewritten_dependencies,
        )
        artifact = await _get_or_create_source_artifact(published, session)
        version = CalcReportVersion(
            reportId=imported.id,
            sourceArtifactId=artifact.id,
            major=node.version.major,
            minor=node.version.minor,
            patch=node.version.patch,
            description=node.version.description,
            publishedByUserId=user_id,
        )
        session.add(version)
        await session.flush()
        imported_versions[node.version.id] = version
        imported_artifacts[node.version.id] = artifact
        rewritten_dependencies_by_version[node.version.id] = rewritten_dependencies

    chosen_nodes: dict[int, SharedVersionNode] = {}
    for original_report_id, report_nodes in nodes_by_report.items():
        imported = imported_reports[original_report_id]
        original_report = report_nodes[0].report
        chosen_node = next(
            (
                node
                for node in report_nodes
                if node.version.id == original_report.latestVersionId
            ),
            report_nodes[0],
        )
        if original_report_id == root_report.id:
            chosen_node = next(
                node for node in report_nodes if node.version.id == root_version.id
            )
        chosen_artifact = imported_artifacts[chosen_node.version.id]
        chosen_version = imported_versions[chosen_node.version.id]
        imported.workspaceArtifactId = chosen_artifact.id
        imported.entryPath = chosen_artifact.manifest["calcbook"]["entryPath"]
        imported.formatVersion = chosen_artifact.manifest["calcbook"]["formatVersion"]
        imported.latestVersionId = chosen_version.id
        chosen_nodes[original_report_id] = chosen_node
    await session.flush()

    for original_report_id, chosen_node in chosen_nodes.items():
        imported = imported_reports[original_report_id]
        dependency_dtos = [
            ReportDependencyDTO.model_validate(value)
            for value in rewritten_dependencies_by_version[chosen_node.version.id]
        ]
        _, dependency_models = await _resolve_dependencies(
            user_id, imported, imported.oid, dependency_dtos, session
        )
        await _replace_dependencies(imported.id, dependency_models, session)
        session.add(
            CalcReportOrigin(
                reportId=imported.id,
                sourceReportId=chosen_node.report.id,
                sourceVersionId=chosen_node.version.id,
                sourceArtifactId=chosen_node.artifact.id,
                originMetadata={"shareLinkOid": link.oid},
            )
        )
    if request.shouldSync and sync_locator is not None:
        root_artifact = imported_artifacts[root_version.id]
        session.add(
            CalcReportSyncSource(
                reportId=imported_reports[root_report.id].id,
                sourceLocator=encrypt_persisted_secret(sync_locator),
                sourceReportOid=root_report.oid,
                sourceVersionName=_version_name(root_version),
                sourceArtifactHash=root_artifact.contentHash,
            )
        )
    await session.commit()
    for node in closure:
        imported_report = imported_reports[node.report.id]
        imported_version = imported_versions[node.version.id]
        imported_artifact = imported_artifacts[node.version.id]
        _materialize_version_projection(
            user_id, imported_report, imported_version, imported_artifact
        )
    for original_report_id, chosen_node in chosen_nodes.items():
        imported_report = imported_reports[original_report_id]
        imported_version = imported_versions[chosen_node.version.id]
        imported_artifact = imported_artifacts[chosen_node.version.id]
        _materialize_workspace_projection(user_id, imported_report, imported_artifact)
        write_latest_projection(user_id, imported_report, imported_version)
    imported_root = imported_reports[root_report.id]
    return ShareImportResDTO(
        reportOid=imported_root.oid,
        versionName=_version_name(imported_versions[root_version.id]),
        importedReportCount=len(imported_reports),
    )


async def _collect_shared_closure(
    root_report: CalcReport,
    root_version: CalcReportVersion,
    session: AsyncSession,
) -> list[SharedVersionNode]:
    """Resolve and validate every transitive version fixed by SOURCE manifests."""
    ordered: list[SharedVersionNode] = []
    visited: set[int] = set()

    async def visit(report: CalcReport, version: CalcReportVersion) -> None:
        """Visit one version and append it before its dependency nodes."""
        if version.id in visited:
            return
        visited.add(version.id)
        artifact = await session.get(CalcReportArtifact, version.sourceArtifactId)
        if artifact is None or artifact.artifactKind != ArtifactKind.SOURCE.value:
            raise_ex("Shared SOURCE artifact not found", code=500)
        ordered.append(SharedVersionNode(report, version, artifact))
        for declaration in artifact.manifest.get("dependencies", []):
            target = await session.scalar(
                select(CalcReport).where(
                    CalcReport.oid == declaration["targetReportOid"],
                    CalcReport.deletedAt.is_(None),
                )
            )
            if target is None:
                raise_ex(
                    "Shared dependency report not found",
                    code=409,
                    error_code=CalcErrorCode.SHARE_NOT_ALLOWED,
                )
            for selector in declaration.get("selectors", []):
                target_version = await _resolve_shared_selector(
                    target, selector, session
                )
                await visit(target, target_version)

    await visit(root_report, root_version)
    return ordered


async def _resolve_shared_selector(
    report: CalcReport, selector: dict, session: AsyncSession
) -> CalcReportVersion:
    """Resolve a latest or explicit selector to one immutable version."""
    if selector["selectorKey"] == ReservedDependencySelectorKey.LATEST:
        version = await session.get(CalcReportVersion, report.latestVersionId)
    else:
        major, minor, patch = parse_version_name(selector["versionName"])
        version = await session.scalar(
            select(CalcReportVersion).where(
                CalcReportVersion.reportId == report.id,
                CalcReportVersion.major == major,
                CalcReportVersion.minor == minor,
                CalcReportVersion.patch == patch,
            )
        )
    if version is None:
        raise_ex("Shared dependency version not found", code=409)
    return cast(CalcReportVersion, version)


async def _authorize_share(
    user_id: int | None, token: str, session: AsyncSession
) -> tuple[CalcReportShareLink, CalcReport, CalcReportVersion]:
    """Validate token state and recipient authorization without consuming it."""
    link = await session.scalar(
        select(CalcReportShareLink).where(
            CalcReportShareLink.tokenHash == _token_hash(token)
        )
    )
    if link is None:
        raise_ex(
            "Share link is unavailable",
            code=404,
            error_code=CalcErrorCode.SHARE_NOT_FOUND,
        )
    return await _authorize_share_link(user_id, link, session)


async def _authorize_share_link(
    user_id: int | None,
    link: CalcReportShareLink,
    session: AsyncSession,
) -> tuple[CalcReportShareLink, CalcReport, CalcReportVersion]:
    """Validate one loaded share against lifecycle and audience rules."""
    now = datetime.datetime.now(datetime.timezone.utc)
    if link.revokedAt is not None or _is_expired(link.expiresAt, now):
        raise_ex(
            "Share link is unavailable",
            code=404,
            error_code=CalcErrorCode.SHARE_NOT_FOUND,
        )
    if link.maxUseCount is not None and link.useCount >= link.maxUseCount:
        raise_ex(
            "Share link use limit has been reached",
            code=409,
            error_code=CalcErrorCode.SHARE_NOT_ALLOWED,
        )
    if link.accessType != DbShareAccessType.PUBLIC.value and user_id is None:
        raise_ex(
            "Authentication is required for this share link",
            code=401,
            error_code=CalcErrorCode.SHARE_NOT_ALLOWED,
        )
    if link.accessType == DbShareAccessType.SPECIFIED_USERS.value:
        recipient = await session.get(CalcReportShareRecipient, (link.id, user_id))
        if recipient is None:
            raise_ex(
                "Share link is not available to this user",
                code=403,
                error_code=CalcErrorCode.SHARE_NOT_ALLOWED,
            )
    if link.accessType == DbShareAccessType.SPECIFIED_DEPARTMENTS.value:
        selected_department_ids = list(
            await session.scalars(
                select(CalcReportShareDepartment.departmentId).where(
                    CalcReportShareDepartment.shareLinkId == link.id
                )
            )
        )
        authorized_department_ids: set[int] = set()
        for department_id in selected_department_ids:
            authorized_department_ids.update(
                await descendant_department_ids(department_id, session)
            )
        membership = await session.scalar(
            select(DepartmentUser.departmentId).where(
                DepartmentUser.userId == user_id,
                DepartmentUser.departmentId.in_(authorized_department_ids),
            )
        )
        if membership is None:
            raise_ex(
                "Share link is not available to this user's departments",
                code=403,
                error_code=CalcErrorCode.SHARE_NOT_ALLOWED,
            )
    version = await session.get(CalcReportVersion, link.versionId)
    report = (
        await session.get(CalcReport, version.reportId) if version is not None else None
    )
    if version is None or report is None or report.deletedAt is not None:
        raise_ex(
            "Shared report is unavailable",
            code=404,
            error_code=CalcErrorCode.SHARE_NOT_FOUND,
        )
    return link, report, version


async def _consume_share(link: CalcReportShareLink, session: AsyncSession) -> None:
    """Atomically consume one available use from a share link."""
    now = datetime.datetime.now(datetime.timezone.utc)
    conditions = [
        CalcReportShareLink.id == link.id,
        CalcReportShareLink.revokedAt.is_(None),
    ]
    if link.expiresAt is not None:
        conditions.append(CalcReportShareLink.expiresAt > now)
    if link.maxUseCount is not None:
        conditions.append(
            CalcReportShareLink.useCount < CalcReportShareLink.maxUseCount
        )
    result = await session.execute(
        update(CalcReportShareLink)
        .where(*conditions)
        .values(useCount=CalcReportShareLink.useCount + 1)
    )
    if result.rowcount != 1:
        await session.rollback()
        raise_ex(
            "Share link is no longer available",
            code=409,
            error_code=CalcErrorCode.SHARE_NOT_ALLOWED,
        )


async def _resolve_recipients(
    recipient_oids: list[str], session: AsyncSession
) -> list[User]:
    """Resolve active recipient OIDs or reject the complete request."""
    if any(not ObjectId.is_valid(oid) for oid in recipient_oids):
        raise_ex("Invalid recipient identifier", code=400)
    if not recipient_oids:
        return []
    recipients = list(
        await session.scalars(
            select(User).where(
                User.oid.in_(recipient_oids), User.status == UserStatus.Active.value
            )
        )
    )
    if len(recipients) != len(recipient_oids):
        raise_ex("Share recipient not found", code=404)
    return recipients


async def _resolve_departments(
    department_oids: list[str], session: AsyncSession
) -> list[Department]:
    """Resolve active department OIDs or reject the complete request.

    Args:
        department_oids: Public department identifiers selected by the owner.
        session: Active database session.

    Returns:
        Active departments in the request.

    Raises:
        CustomException: If an identifier is invalid or unavailable.
    """
    if any(not ObjectId.is_valid(oid) for oid in department_oids):
        raise_ex("Invalid department identifier", code=400)
    if not department_oids:
        return []
    departments = list(
        await session.scalars(
            select(Department).where(
                Department.oid.in_(department_oids), Department.deletedAt.is_(None)
            )
        )
    )
    if len(departments) != len(department_oids):
        raise_ex("Share department not found", code=404)
    return departments


async def _get_owned_report(
    user_id: int, report_oid: str, session: AsyncSession
) -> CalcReport:
    """Load one active owned report for sharing."""
    report = await session.scalar(
        select(CalcReport).where(
            CalcReport.oid == report_oid,
            CalcReport.userId == user_id,
            CalcReport.deletedAt.is_(None),
        )
    )
    if report is None:
        raise_ex(
            "Report not found", code=404, error_code=CalcErrorCode.REPORT_NOT_FOUND
        )
    return cast(CalcReport, report)


async def _get_version(
    report: CalcReport, version_name: str, session: AsyncSession
) -> CalcReportVersion:
    """Load one strict semantic version owned by a report."""
    try:
        major, minor, patch = parse_version_name(version_name)
    except ValueError as error:
        raise_ex(str(error), code=400)
    version = await session.scalar(
        select(CalcReportVersion).where(
            CalcReportVersion.reportId == report.id,
            CalcReportVersion.major == major,
            CalcReportVersion.minor == minor,
            CalcReportVersion.patch == patch,
        )
    )
    if version is None:
        raise_ex("Report version not found", code=404)
    return cast(CalcReportVersion, version)


async def _get_owned_share(
    user_id: int, share_oid: str, session: AsyncSession
) -> tuple[CalcReportShareLink, CalcReport, CalcReportVersion]:
    """Load a share link through its version/report ownership chain."""
    row = (
        await session.execute(
            select(CalcReportShareLink, CalcReport, CalcReportVersion)
            .join(
                CalcReportVersion, CalcReportVersion.id == CalcReportShareLink.versionId
            )
            .join(CalcReport, CalcReport.id == CalcReportVersion.reportId)
            .where(
                CalcReportShareLink.oid == share_oid,
                CalcReport.userId == user_id,
            )
        )
    ).one_or_none()
    if row is None:
        raise_ex(
            "Share link not found",
            code=404,
            error_code=CalcErrorCode.SHARE_NOT_FOUND,
        )
    return row


async def _available_report_name(
    user_id: int, category_id: int, preferred: str, session: AsyncSession
) -> str:
    """Return a deterministic non-conflicting active report name."""
    base = preferred.strip()[:100] or "Imported report"
    candidate = base
    suffix = 2
    while await session.scalar(
        select(CalcReport.id).where(
            CalcReport.userId == user_id,
            CalcReport.categoryId == category_id,
            CalcReport.name == candidate,
            CalcReport.deletedAt.is_(None),
        )
    ):
        marker = f" ({suffix})"
        candidate = f"{base[: 100 - len(marker)]}{marker}"
        suffix += 1
    return candidate


def _share_link_response(
    link: CalcReportShareLink,
    report: CalcReport,
    version: CalcReportVersion,
    *,
    token: str | None = None,
    recipient_user_oids: list[str] | None = None,
    recipient_department_oids: list[str] | None = None,
) -> ShareLinkResDTO:
    """Convert share/version/report models to a public response."""
    return ShareLinkResDTO(
        shareOid=link.oid,
        reportOid=report.oid,
        versionName=_version_name(version),
        accessType=ShareAccessType[DbShareAccessType(link.accessType).name],
        canEdit=link.canEdit,
        canShare=link.canShare,
        recipientUserOids=recipient_user_oids or [],
        recipientDepartmentOids=recipient_department_oids or [],
        note=link.note,
        expiresAt=link.expiresAt,
        revokedAt=link.revokedAt,
        maxUseCount=link.maxUseCount,
        useCount=link.useCount,
        createdAt=link.createdAt,
        token=token,
    )


async def _share_recipient_oids(
    share_link_id: int, session: AsyncSession
) -> tuple[list[str], list[str]]:
    """Resolve public recipient identifiers for one share link.

    Args:
        share_link_id: Internal share-link identifier.
        session: Active database session.

    Returns:
        User OIDs and department OIDs in stable order.

    Raises:
        SQLAlchemyError: If recipient lookup fails.
    """
    user_oids = list(
        (
            await session.scalars(
                select(User.oid)
                .join(
                    CalcReportShareRecipient,
                    CalcReportShareRecipient.userId == User.id,
                )
                .where(CalcReportShareRecipient.shareLinkId == share_link_id)
                .order_by(User.id)
            )
        ).all()
    )
    department_oids = list(
        (
            await session.scalars(
                select(Department.oid)
                .join(
                    CalcReportShareDepartment,
                    CalcReportShareDepartment.departmentId == Department.id,
                )
                .where(CalcReportShareDepartment.shareLinkId == share_link_id)
                .order_by(Department.id)
            )
        ).all()
    )
    return user_oids, department_oids


def _version_name(version: CalcReportVersion) -> str:
    """Derive a semantic version string from immutable numeric fields."""
    return f"{version.major}.{version.minor}.{version.patch}"


def _token_hash(token: str) -> str:
    """Hash a bearer token before database lookup or persistence."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _is_expired(expires_at: datetime.datetime | None, now: datetime.datetime) -> bool:
    """Compare database timestamps while tolerating SQLite naive values."""
    if expires_at is None:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
    return expires_at <= now
