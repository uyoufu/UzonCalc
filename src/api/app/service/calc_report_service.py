"""Metadata, copy, soft-delete, and favorite services for CalcReport."""

import datetime
import hashlib
from pathlib import Path
import shutil
from typing import Any

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_state import (
    BuildStatus,
    PublishState,
    ReportOriginType as PublicReportOriginType,
    ReportSyncState,
)
from app.controller.calc.calc_report_dto import (
    CalcReportCopyDTO,
    CalcReportListFilterDTO,
    CalcReportResDTO,
    CalcReportUpdateDTO,
)
from app.controller.dto_base import PaginationDTO
from app.db.models.calc_report import CalcReport, CalcReportOrigin, CalcReportSyncSource
from app.db.models.calc_report_artifact import CalcReportArtifact
from app.db.models.calc_report_category import CalcReportCategory
from app.db.models.calc_report_dependency import (
    CalcReportDependency,
    CalcReportDependencySelector,
)
from app.db.models.calc_report_version import CalcReportVersion
from app.db.models.calc_report_share import CalcReportShareLink
from app.db.models.calc_report_instance import CalcReportInstance
from app.db.models.calc_execution import CalcExecution, CalcExecutionSlot
from app.db.models.enums import ReportOriginType
from app.db.models.favorite_calc_report import FavoriteCalcReport
from app.db.models.object_id import ObjectId
from app.exception.custom_exception import raise_ex
from app.service.calc_report_artifact_service import public_hash
from app.service.calc_report_category_service import get_category
from app.service.calc_report_build_service import (
    configured_runtime_fingerprint_hint,
    get_build_state,
)
from app.service.calc_report_workspace_service import get_owned_report, get_workspace
from app.service.secret_storage_service import decrypt_persisted_secret
from config import app_config


async def count_reports(
    user_id: int,
    filters: CalcReportListFilterDTO,
    session: AsyncSession,
) -> int:
    """Count active owned reports matching the supplied filters."""
    conditions = await _report_list_conditions(user_id, filters, session)
    total = await session.scalar(select(func.count(CalcReport.id)).where(*conditions))
    return total or 0


async def list_reports(
    user_id: int,
    filters: CalcReportListFilterDTO,
    pagination: PaginationDTO,
    session: AsyncSession,
) -> list[CalcReportResDTO]:
    """List one sorted page of active owned reports."""
    conditions = await _report_list_conditions(user_id, filters, session)
    sort_columns = {
        "id": CalcReport.id,
        "name": CalcReport.name,
        "createdAt": CalcReport.createdAt,
        "updatedAt": CalcReport.updatedAt,
    }
    sort_column = sort_columns.get(pagination.sortBy, CalcReport.updatedAt)
    sort_expression = sort_column.desc() if pagination.descending else sort_column.asc()
    stable_sort = CalcReport.id.desc() if pagination.descending else CalcReport.id.asc()
    reports = (
        await session.scalars(
            select(CalcReport)
            .where(*conditions)
            .order_by(sort_expression, stable_sort)
            .offset(pagination.skip)
            .limit(pagination.limit)
        )
    ).all()
    return [await _report_response(report, session) for report in reports]


async def _report_list_conditions(
    user_id: int,
    filters: CalcReportListFilterDTO,
    session: AsyncSession,
) -> list[Any]:
    """Build the shared report predicates used by count and item queries."""
    conditions = [
        CalcReport.userId == user_id,
        CalcReport.deletedAt.is_(None),
        CalcReport.isSystemComponent.is_(False),
    ]
    if filters.categoryOid:
        category = await get_category(user_id, filters.categoryOid, session)
        conditions.append(CalcReport.categoryId == category.id)
    if filters.favoriteOnly:
        favorite_report_ids = select(FavoriteCalcReport.reportId).where(
            FavoriteCalcReport.userId == user_id
        )
        conditions.append(CalcReport.id.in_(favorite_report_ids))
    if filters.query:
        pattern = f"%{filters.query.strip()}%"
        conditions.append(
            CalcReport.name.ilike(pattern) | CalcReport.description.ilike(pattern)
        )
    return conditions


async def get_report(
    user_id: int, report_oid: str, session: AsyncSession
) -> CalcReportResDTO:
    """Return one active owned report with derived state."""
    report = await get_owned_report(user_id, report_oid, session)
    return await _report_response(report, session)


async def update_report(
    user_id: int,
    report_oid: str,
    request: CalcReportUpdateDTO,
    session: AsyncSession,
) -> CalcReportResDTO:
    """Update report display metadata without moving workspace storage."""
    report = await get_owned_report(user_id, report_oid, session)
    category = await get_category(user_id, request.categoryOid, session)
    duplicate = await session.scalar(
        select(CalcReport.id).where(
            CalcReport.userId == user_id,
            CalcReport.categoryId == category.id,
            CalcReport.name == request.name.strip(),
            CalcReport.id != report.id,
            CalcReport.deletedAt.is_(None),
        )
    )
    if duplicate is not None:
        raise_ex("Report name already exists in this category", code=409)
    report.categoryId = category.id
    report.name = request.name.strip()
    report.description = request.description
    report.cover = request.cover
    await session.commit()
    await session.refresh(report)
    return await _report_response(report, session)


async def copy_report(
    user_id: int,
    source_report_oid: str,
    request: CalcReportCopyDTO,
    session: AsyncSession,
) -> CalcReportResDTO:
    """Copy an owned workspace and its mutable dependency declarations."""
    source = await get_owned_report(user_id, source_report_oid, session)
    source_workspace = get_workspace_projection_path(user_id, source_report_oid)
    if not source_workspace.is_dir():
        raise_ex(
            "Workspace not found",
            code=404,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
    await get_workspace(user_id, source_report_oid, session)
    category = await get_category(user_id, request.categoryOid, session)
    target_oid = request.reportOid or ObjectId().to_hex()
    if not ObjectId.is_valid(target_oid):
        raise_ex(
            "Invalid report identifier",
            code=400,
            error_code=CalcErrorCode.INVALID_OBJECT_ID,
        )
    existing = await session.scalar(
        select(CalcReport.id).where(CalcReport.oid == target_oid)
    )
    if existing is not None:
        raise_ex("Report identifier already exists", code=409)
    target = CalcReport(
        oid=target_oid,
        userId=user_id,
        categoryId=category.id,
        name=request.name.strip(),
        description=request.description,
        cover=request.cover,
        entryPath=source.entryPath,
        formatVersion=source.formatVersion,
        workspaceRevision=1,
        workspaceHash=source.workspaceHash,
        workspaceManifest=source.workspaceManifest,
        workspaceArtifactId=source.workspaceArtifactId,
        originType=ReportOriginType.COPY.value,
        canEdit=source.canEdit,
        canShare=source.canShare,
    )
    session.add(target)
    await session.flush()
    session.add(
        CalcReportOrigin(
            reportId=target.id,
            sourceReportId=source.id,
            sourceArtifactId=source.workspaceArtifactId,
        )
    )
    dependencies = (
        await session.scalars(
            select(CalcReportDependency).where(
                CalcReportDependency.reportId == source.id
            )
        )
    ).all()
    for dependency in dependencies:
        copied = CalcReportDependency(
            reportId=target.id,
            targetReportId=dependency.targetReportId,
            alias=dependency.alias,
        )
        session.add(copied)
        await session.flush()
        selectors = (
            await session.scalars(
                select(CalcReportDependencySelector).where(
                    CalcReportDependencySelector.dependencyId == dependency.id
                )
            )
        ).all()
        for selector in selectors:
            session.add(
                CalcReportDependencySelector(
                    dependencyId=copied.id,
                    targetReportId=selector.targetReportId,
                    selectorKey=selector.selectorKey,
                    targetVersionId=selector.targetVersionId,
                    isDefault=selector.isDefault,
                )
            )
    target_workspace = get_workspace_projection_path(user_id, target.oid)
    try:
        shutil.copytree(source_workspace, target_workspace)
        await session.commit()
    except Exception:
        await session.rollback()
        shutil.rmtree(target_workspace, ignore_errors=True)
        raise
    return await _report_response(target, session)


async def delete_report(
    user_id: int,
    report_oid: str,
    session: AsyncSession,
    *,
    include_deleted: bool = False,
) -> None:
    """Delete an owned report while retaining identities required by instances.

    Args:
        user_id: Current user database ID.
        report_oid: Owned report identifier.
        session: Database session used for dependency checks and deletion.
        include_deleted: Whether an internal final purge may load a soft-deleted report.

    Returns:
        None.

    Raises:
        CustomException: If another report still depends on this report.
    """
    report = await get_owned_report(
        user_id, report_oid, session, include_deleted=include_deleted
    )
    dependent_report_count = await session.scalar(
        select(func.count(CalcReportDependency.id)).where(
            CalcReportDependency.targetReportId == report.id
        )
    )
    if dependent_report_count:
        raise_ex(
            "Report is still referenced by calculation dependencies",
            code=409,
            data={"dependentReportCount": dependent_report_count},
        )
    version_ids = list(
        await session.scalars(
            select(CalcReportVersion.id).where(CalcReportVersion.reportId == report.id)
        )
    )
    share_ids = list(
        await session.scalars(
            select(CalcReportShareLink.id).where(
                CalcReportShareLink.reportId == report.id
            )
        )
    )
    slot_conditions = [CalcExecutionSlot.reportId == report.id]
    if version_ids:
        slot_conditions.append(CalcExecutionSlot.versionId.in_(version_ids))
    if share_ids:
        slot_conditions.append(CalcExecutionSlot.shareLinkId.in_(share_ids))
    slots = list(
        await session.scalars(select(CalcExecutionSlot).where(or_(*slot_conditions)))
    )
    from app.service.calc_execution_service import discard_execution_slot

    for slot in slots:
        await discard_execution_slot(slot, session)
        await session.delete(slot)
    await session.flush()
    retained_instance_execution_ids = {
        execution_id
        for row in await session.execute(
            select(
                CalcExecutionSlot.activeExecutionId,
                CalcExecutionSlot.currentExecutionId,
            ).where(CalcExecutionSlot.instanceId.is_not(None))
        )
        for execution_id in row
        if execution_id is not None
    }
    execution_delete = delete(CalcExecution).where(CalcExecution.reportId == report.id)
    if retained_instance_execution_ids:
        execution_delete = execution_delete.where(
            CalcExecution.id.not_in(retained_instance_execution_ids)
        )
    await session.execute(execution_delete)
    await session.execute(
        delete(CalcReportShareLink).where(CalcReportShareLink.reportId == report.id)
    )
    await session.execute(
        delete(FavoriteCalcReport).where(
            FavoriteCalcReport.userId == user_id,
            FavoriteCalcReport.reportId == report.id,
        )
    )
    instance_count = await session.scalar(
        select(func.count(CalcReportInstance.id)).where(
            CalcReportInstance.reportId == report.id
        )
    )
    if instance_count:
        report.deletedAt = datetime.datetime.now(datetime.timezone.utc)
        report.workspaceArtifactId = None
        report.workspaceHash = None
        report.workspaceManifest = None
        await session.execute(
            update(CalcReportOrigin)
            .where(CalcReportOrigin.reportId == report.id)
            .values(sourceArtifactId=None)
        )
    else:
        report.latestVersionId = None
        await session.flush()
        await session.execute(
            update(CalcReportOrigin)
            .where(CalcReportOrigin.sourceReportId == report.id)
            .values(sourceReportId=None)
        )
        if version_ids:
            await session.execute(
                update(CalcReportOrigin)
                .where(CalcReportOrigin.sourceVersionId.in_(version_ids))
                .values(sourceVersionId=None)
            )
        await session.execute(
            delete(CalcReportVersion).where(CalcReportVersion.reportId == report.id)
        )
        await session.delete(report)
    await session.commit()
    shutil.rmtree(
        get_workspace_projection_path(user_id, report_oid).parent,
        ignore_errors=True,
    )


async def set_favorite(
    user_id: int, report_oid: str, is_favorite: bool, session: AsyncSession
) -> CalcReportResDTO:
    """Create or delete the current user's report favorite association."""
    report = await get_owned_report(user_id, report_oid, session)
    favorite = await session.get(FavoriteCalcReport, (user_id, report.id))
    if is_favorite and favorite is None:
        session.add(FavoriteCalcReport(userId=user_id, reportId=report.id))
    elif not is_favorite and favorite is not None:
        await session.delete(favorite)
    await session.commit()
    return await _report_response(report, session)


def get_workspace_projection_path(user_id: int, report_oid: str) -> Path:
    """Return an OID-based readable workspace projection path."""
    return (
        Path(app_config.calc_report_reports_root)
        / str(user_id)
        / report_oid
        / "workspace"
    ).resolve()


async def _report_response(
    report: CalcReport, session: AsyncSession
) -> CalcReportResDTO:
    """Build report response fields from normalized database relationships."""
    category = await session.get(CalcReportCategory, report.categoryId)
    workspace_artifact = (
        await session.get(CalcReportArtifact, report.workspaceArtifactId)
        if report.workspaceArtifactId is not None
        else None
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
    runtime_fingerprint = configured_runtime_fingerprint_hint()
    build_status = (
        (await get_build_state(workspace_artifact.id, runtime_fingerprint, session))[0]
        if workspace_artifact is not None and runtime_fingerprint is not None
        else BuildStatus.NOT_REQUESTED
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
    is_favorite = (
        await session.get(FavoriteCalcReport, (report.userId, report.id)) is not None
    )
    latest_name = (
        f"{latest.major}.{latest.minor}.{latest.patch}" if latest is not None else None
    )
    return CalcReportResDTO(
        reportOid=report.oid,
        categoryOid=category.oid if category is not None else "",
        name=report.name,
        description=report.description,
        cover=report.cover,
        entryPath=report.entryPath,
        formatVersion=report.formatVersion,
        workspaceRevision=report.workspaceRevision,
        workspaceHash=public_hash(report.workspaceHash)
        if report.workspaceHash
        else None,
        latestVersionName=latest_name,
        latestArtifactHash=(
            public_hash(latest_artifact.contentHash)
            if latest_artifact is not None
            else None
        ),
        buildStatus=build_status,
        publishState=publish_state,
        isFavorite=is_favorite,
        originType=PublicReportOriginType[ReportOriginType(report.originType).name],
        syncState=await _report_sync_state(report, session),
        canEdit=report.canEdit,
        canShare=report.canShare,
        createdAt=report.createdAt,
        updatedAt=report.updatedAt,
    )


async def _report_sync_state(
    report: CalcReport, session: AsyncSession
) -> ReportSyncState:
    """Derive cheap same-backend synchronization state for report lists."""
    if report.originType != ReportOriginType.SHARE_SYNC.value:
        return ReportSyncState.NOT_APPLICABLE
    sync_source = await session.scalar(
        select(CalcReportSyncSource).where(CalcReportSyncSource.reportId == report.id)
    )
    if sync_source is None:
        return ReportSyncState.SOURCE_UNAVAILABLE
    try:
        token = decrypt_persisted_secret(sync_source.sourceLocator)
    except ValueError:
        return ReportSyncState.SOURCE_UNAVAILABLE
    link = (
        await session.scalar(
            select(CalcReportShareLink).where(
                CalcReportShareLink.oid == token.removeprefix("catalog:")
            )
        )
        if token.startswith("catalog:")
        else await session.scalar(
            select(CalcReportShareLink).where(
                CalcReportShareLink.tokenHash
                == hashlib.sha256(token.encode("utf-8")).hexdigest()
            )
        )
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    if link is None or link.revokedAt is not None:
        return ReportSyncState.ACCESS_REVOKED
    expires_at = link.expiresAt
    if expires_at is not None:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
        if expires_at <= now:
            return ReportSyncState.ACCESS_REVOKED
    source_report = await session.scalar(
        select(CalcReport).where(
            CalcReport.oid == sync_source.sourceReportOid,
            CalcReport.deletedAt.is_(None),
        )
    )
    if source_report is None or source_report.latestVersionId is None:
        return ReportSyncState.SOURCE_UNAVAILABLE
    source_version = await session.get(CalcReportVersion, source_report.latestVersionId)
    source_artifact = (
        await session.get(CalcReportArtifact, source_version.sourceArtifactId)
        if source_version is not None
        else None
    )
    if source_artifact is None:
        return ReportSyncState.SOURCE_UNAVAILABLE
    return (
        ReportSyncState.CURRENT
        if source_artifact.contentHash == sync_source.sourceArtifactHash
        else ReportSyncState.UPDATE_AVAILABLE
    )
