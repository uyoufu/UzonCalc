"""Metadata, copy, soft-delete, and favorite services for CalcReport."""

import datetime
import json
from pathlib import Path
from typing import Any, cast

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_report_dto import (
    CalcReportCopyDTO,
    CalcReportListFilterDTO,
    CalcReportResDTO,
    CalcReportUpdateDTO,
)
from app.controller.dto_base import PaginationDTO
from app.db.models.calc_report import CalcReport, CalcReportOrigin
from app.db.models.calc_report_artifact import (
    CalcReportArtifact,
    CalcReportArtifactBuild,
)
from app.db.models.calc_report_category import CalcReportCategory
from app.db.models.calc_report_dependency import (
    CalcReportDependency,
    CalcReportDependencySelector,
)
from app.db.models.calc_report_version import CalcReportVersion
from app.db.models.enums import ArtifactBuildStatus, ReportOriginType
from app.db.models.favorite_calc_report import FavoriteCalcReport
from app.db.models.object_id import ObjectId
from app.exception.custom_exception import raise_ex
from app.service.calc_report_artifact_service import artifact_store, public_hash
from app.service.calc_report_category_service import get_category
from app.service.calc_report_build_service import configured_runtime_fingerprint_hint
from app.service.calc_report_workspace_service import get_owned_report
from config import app_config, logger


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
    conditions = [CalcReport.userId == user_id, CalcReport.deletedAt.is_(None)]
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
    if source.workspaceArtifactId is None:
        raise_ex(
            "Workspace not found",
            code=404,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
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
        workspaceArtifactId=source.workspaceArtifactId,
    )
    session.add(target)
    await session.flush()
    session.add(
        CalcReportOrigin(
            reportId=target.id,
            originType=ReportOriginType.COPY.value,
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
    await session.commit()
    artifact = await session.get(CalcReportArtifact, source.workspaceArtifactId)
    if artifact is not None:
        _materialize_report_workspace(user_id, target, artifact)
    return await _report_response(target, session)


async def delete_report(user_id: int, report_oid: str, session: AsyncSession) -> None:
    """Soft-delete an owned report and remove its favorite association."""
    report = await get_owned_report(user_id, report_oid, session)
    report.deletedAt = datetime.datetime.now(datetime.timezone.utc)
    await session.execute(
        delete(FavoriteCalcReport).where(
            FavoriteCalcReport.userId == user_id,
            FavoriteCalcReport.reportId == report.id,
        )
    )
    await session.commit()


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
    build = None
    runtime_fingerprint = configured_runtime_fingerprint_hint()
    if workspace_artifact is not None and runtime_fingerprint is not None:
        build = await session.scalar(
            select(CalcReportArtifactBuild).where(
                CalcReportArtifactBuild.sourceArtifactId == workspace_artifact.id,
                CalcReportArtifactBuild.runtimeFingerprint == runtime_fingerprint,
            )
        )
    build_status = (
        ArtifactBuildStatus(build.status).name.lower()
        if build is not None
        else "not_requested"
    )
    publish_state = "unpublished"
    if latest is not None and workspace_artifact is not None:
        if latest.sourceArtifactId == workspace_artifact.id:
            publish_state = "published"
        else:
            matches_version = await session.scalar(
                select(CalcReportVersion.id).where(
                    CalcReportVersion.reportId == report.id,
                    CalcReportVersion.sourceArtifactId == workspace_artifact.id,
                )
            )
            publish_state = (
                "workspace_version_mismatch"
                if matches_version is not None
                else "unpublished_changes"
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
        workspaceArtifactHash=(
            public_hash(workspace_artifact.contentHash)
            if workspace_artifact is not None
            else None
        ),
        latestVersionName=latest_name,
        latestArtifactHash=(
            public_hash(latest_artifact.contentHash)
            if latest_artifact is not None
            else None
        ),
        buildStatus=build_status,
        publishState=publish_state,
        isFavorite=is_favorite,
        createdAt=report.createdAt,
        updatedAt=report.updatedAt,
    )


def _materialize_report_workspace(
    user_id: int, report: CalcReport, artifact: CalcReportArtifact
) -> None:
    """Materialize a copied report's readable workspace projection."""
    try:
        artifact_store.materialize(
            artifact.storageKey, get_workspace_projection_path(user_id, report.oid)
        )
    except OSError:
        logger.exception("Failed to materialize copied report %s", report.oid)


def write_latest_projection(
    user_id: int, report: CalcReport, version: CalcReportVersion
) -> None:
    """Write the recoverable latest.json projection for a report."""
    report_root = get_workspace_projection_path(user_id, report.oid).parent
    report_root.mkdir(parents=True, exist_ok=True)
    temporary = report_root / ".latest.json.tmp"
    temporary.write_text(
        json.dumps(
            {
                "reportOid": report.oid,
                "versionName": f"{version.major}.{version.minor}.{version.patch}",
                "versionOid": version.oid,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary.replace(report_root / "latest.json")
