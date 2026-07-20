"""Derive public calculation-report states from persisted models."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_state import PublishState
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_artifact import CalcReportArtifact
from app.db.models.calc_report_version import CalcReportVersion


async def resolve_publish_state(
    report: CalcReport,
    workspace_artifact: CalcReportArtifact,
    session: AsyncSession,
) -> PublishState:
    """Resolve the workspace relationship to the report's published versions.

    Args:
        report: Report that owns the mutable workspace.
        workspace_artifact: Current immutable workspace snapshot.
        session: Database session used to inspect published versions.

    Returns:
        Strongly typed public publication state.

    Raises:
        SQLAlchemyError: If the database query fails.
    """
    if report.latestVersionId is None:
        return PublishState.UNPUBLISHED

    latest = await session.get(CalcReportVersion, report.latestVersionId)
    if latest is not None and latest.sourceArtifactId == workspace_artifact.id:
        return PublishState.PUBLISHED

    matching_version = await session.scalar(
        select(CalcReportVersion.id).where(
            CalcReportVersion.reportId == report.id,
            CalcReportVersion.sourceArtifactId == workspace_artifact.id,
        )
    )
    if matching_version is not None:
        return PublishState.WORKSPACE_VERSION_MISMATCH
    return PublishState.UNPUBLISHED_CHANGES
