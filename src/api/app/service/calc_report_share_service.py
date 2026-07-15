"""Approved-version share links and full dependency-closure imports."""

from __future__ import annotations

import datetime
import hashlib
import secrets
from dataclasses import dataclass
from typing import cast

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_share_dto import (
    ShareImportDTO,
    ShareImportResDTO,
    ShareLinkCreateDTO,
    ShareLinkResDTO,
    SharePreviewResDTO,
)
from app.controller.calc.calc_workspace_dto import ReportDependencyDTO
from app.db.models.calc_report import CalcReport, CalcReportOrigin
from app.db.models.calc_report_artifact import CalcReportArtifact
from app.db.models.calc_report_category import CalcReportCategory
from app.db.models.calc_report_dependency import CalcReportDependency
from app.db.models.calc_report_share import (
    CalcReportShareLink,
    CalcReportShareRecipient,
)
from app.db.models.calc_report_version import CalcReportVersion
from app.db.models.enums import (
    ArtifactKind,
    ReportOriginType,
    ShareAccessType,
    VersionReviewStatus,
)
from app.db.models.object_id import ObjectId
from app.db.models.user import User, UserStatus
from app.exception.custom_exception import raise_ex
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


@dataclass(frozen=True)
class SharedVersionNode:
    """Hold one approved report/version/artifact node in an import closure."""

    report: CalcReport
    version: CalcReportVersion
    artifact: CalcReportArtifact


async def create_share_link(
    user_id: int,
    report_oid: str,
    request: ShareLinkCreateDTO,
    session: AsyncSession,
) -> ShareLinkResDTO:
    """Create a secret link for an approved version and return its token once."""
    report = await _get_owned_report(user_id, report_oid, session)
    version = await _get_version(report, request.versionName, session)
    if version.reviewStatus != VersionReviewStatus.APPROVED.value:
        raise_ex(
            "Only approved versions can be shared",
            code=409,
            error_code=CalcErrorCode.SHARE_NOT_ALLOWED,
        )
    await _collect_approved_closure(report, version, session)
    recipients = await _resolve_recipients(request.recipientUserOids, session)
    token = secrets.token_urlsafe(32)
    access_type = ShareAccessType[request.accessType.upper()]
    link = CalcReportShareLink(
        versionId=version.id,
        tokenHash=_token_hash(token),
        accessType=access_type.value,
        expiresAt=request.expiresAt,
        maxUseCount=request.maxUseCount,
        createdByUserId=user_id,
    )
    session.add(link)
    await session.flush()
    for recipient in recipients:
        session.add(CalcReportShareRecipient(shareLinkId=link.id, userId=recipient.id))
    await session.commit()
    await session.refresh(link)
    return _share_link_response(link, report, version, token=token)


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
    return [_share_link_response(link, report, version) for link, version in rows]


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
    user_id: int, token: str, session: AsyncSession
) -> SharePreviewResDTO:
    """Validate share authorization and return its full approved footprint."""
    _, report, version = await _authorize_share(user_id, token, session)
    closure = await _collect_approved_closure(report, version, session)
    return SharePreviewResDTO(
        reportName=report.name,
        reportDescription=report.description,
        reportOid=report.oid,
        versionName=_version_name(version),
        dependencyCount=max(0, len(closure) - 1),
        totalFileCount=sum(node.artifact.fileCount for node in closure),
        totalSize=sum(node.artifact.totalSize for node in closure),
    )


async def import_share(
    user_id: int,
    token: str,
    request: ShareImportDTO,
    session: AsyncSession,
) -> ShareImportResDTO:
    """Import a full approved closure as receiver-owned reports and versions."""
    link, root_report, root_version = await _authorize_share(user_id, token, session)
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
    closure = await _collect_approved_closure(root_report, root_version, session)
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
            reviewStatus=VersionReviewStatus.PENDING.value,
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
                originType=ReportOriginType.SHARE.value,
                sourceReportId=chosen_node.report.id,
                sourceVersionId=chosen_node.version.id,
                sourceArtifactId=chosen_node.artifact.id,
                originMetadata={"shareLinkOid": link.oid},
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


async def _collect_approved_closure(
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
        if version.reviewStatus != VersionReviewStatus.APPROVED.value:
            raise_ex(
                "Shared dependency version is not approved",
                code=409,
                error_code=CalcErrorCode.SHARE_NOT_ALLOWED,
            )
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
    if selector["selectorKey"] == "latest":
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
    user_id: int, token: str, session: AsyncSession
) -> tuple[CalcReportShareLink, CalcReport, CalcReportVersion]:
    """Validate token state and recipient authorization without consuming it."""
    link = await session.scalar(
        select(CalcReportShareLink).where(
            CalcReportShareLink.tokenHash == _token_hash(token)
        )
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    if link is None or link.revokedAt is not None or _is_expired(link.expiresAt, now):
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
    if link.accessType == ShareAccessType.SPECIFIED_USERS.value:
        recipient = await session.get(CalcReportShareRecipient, (link.id, user_id))
        if recipient is None:
            raise_ex(
                "Share link is not available to this user",
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
) -> ShareLinkResDTO:
    """Convert share/version/report models to a public response."""
    return ShareLinkResDTO(
        shareOid=link.oid,
        reportOid=report.oid,
        versionName=_version_name(version),
        accessType=ShareAccessType(link.accessType).name.lower(),
        expiresAt=link.expiresAt,
        revokedAt=link.revokedAt,
        maxUseCount=link.maxUseCount,
        useCount=link.useCount,
        createdAt=link.createdAt,
        token=token,
    )


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
