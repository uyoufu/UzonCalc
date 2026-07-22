"""Scheduled cleanup for orphaned calculation artifact and bundle caches."""

import datetime
import logging
import shutil
import stat
from pathlib import Path

from sqlalchemy import delete, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.manager import get_db_manager
from app.db.models.calc_execution import (
    CalcExecution,
    CalcExecutionBundle,
    CalcExecutionBundleComponent,
)
from app.db.models.calc_report import CalcReport, CalcReportOrigin
from app.db.models.calc_report_artifact import (
    CalcReportArtifact,
    CalcReportArtifactBuild,
)
from app.db.models.calc_report_instance import CalcReportInstance
from app.db.models.calc_report_version import CalcReportVersion
from app.db.models.enums import ArtifactBuildStatus
from app.schedule.cron_schedule_job import BaseCronScheduleJob
from config import app_config

_ORPHAN_GRACE_PERIOD = datetime.timedelta(hours=24)


class CalcCacheCleanerScheduleJob(BaseCronScheduleJob):
    """Prune unreferenced cache rows and remove aged orphan directories."""

    def __init__(self) -> None:
        """Configure the calculation-cache cleanup to run daily at 03:20 UTC."""
        super().__init__("calc_cache_cleaner_schedule_job", "0 20 3 * * *")

    async def run_async(self) -> None:
        """Prune unreferenced rows, then remove sufficiently old disk orphans."""
        logger = logging.getLogger("apscheduler")
        async with get_db_manager().session() as session:
            (
                removed_bundle_rows,
                removed_build_rows,
                removed_artifact_rows,
            ) = await _prune_unreferenced_cache_rows(session)
            artifact_hashes = set(
                await session.scalars(select(CalcReportArtifact.contentHash))
            )
            bundle_hashes = set(
                await session.scalars(select(CalcExecutionBundle.bundleHash))
            )
        removed_artifacts = _remove_orphan_hash_directories(
            Path(app_config.calc_report_artifacts_root) / "sha256", artifact_hashes
        )
        removed_bundles = _remove_orphan_hash_directories(
            Path(app_config.calc_report_bundles_root) / "sha256", bundle_hashes
        )
        logger.info(
            "Calculation cache cleanup completed - bundle rows: %s, build rows: %s, "
            "artifact rows: %s, artifact directories: %s, bundle directories: %s",
            removed_bundle_rows,
            removed_build_rows,
            removed_artifact_rows,
            removed_artifacts,
            removed_bundles,
        )


async def _prune_unreferenced_cache_rows(
    session: AsyncSession,
) -> tuple[int, int, int]:
    """Delete immutable cache metadata that has no remaining business owner.

    Args:
        session: Database session used for reference-safe bulk deletion.

    Returns:
        Deleted bundle, build, and artifact row counts.

    Raises:
        SQLAlchemyError: If the transactional cleanup cannot be completed.
    """
    cutoff = datetime.datetime.now(datetime.timezone.utc) - _ORPHAN_GRACE_PERIOD
    bundle_result = await session.execute(
        delete(CalcExecutionBundle).where(
            CalcExecutionBundle.createdAt < cutoff,
            ~exists(
                select(CalcExecution.id).where(
                    CalcExecution.bundleId == CalcExecutionBundle.id
                )
            ),
            ~exists(
                select(CalcReportInstance.id).where(
                    CalcReportInstance.bundleId == CalcExecutionBundle.id
                )
            ),
        )
    )
    build_result = await session.execute(
        delete(CalcReportArtifactBuild).where(
            CalcReportArtifactBuild.updatedAt < cutoff,
            CalcReportArtifactBuild.status != ArtifactBuildStatus.BUILDING.value,
            ~exists(
                select(CalcExecutionBundle.id).where(
                    CalcExecutionBundle.entryExecutionArtifactId
                    == CalcReportArtifactBuild.outputArtifactId
                )
            ),
            ~exists(
                select(CalcExecutionBundleComponent.id).where(
                    CalcExecutionBundleComponent.executionArtifactId
                    == CalcReportArtifactBuild.outputArtifactId
                )
            ),
        )
    )
    artifact_result = await session.execute(
        delete(CalcReportArtifact).where(
            CalcReportArtifact.createdAt < cutoff,
            ~exists(
                select(CalcReport.id).where(
                    CalcReport.workspaceArtifactId == CalcReportArtifact.id
                )
            ),
            ~exists(
                select(CalcReportVersion.id).where(
                    CalcReportVersion.sourceArtifactId == CalcReportArtifact.id
                )
            ),
            ~exists(
                select(CalcReportOrigin.id).where(
                    CalcReportOrigin.sourceArtifactId == CalcReportArtifact.id
                )
            ),
            ~exists(
                select(CalcExecutionBundle.id).where(
                    or_(
                        CalcExecutionBundle.entrySourceArtifactId
                        == CalcReportArtifact.id,
                        CalcExecutionBundle.entryExecutionArtifactId
                        == CalcReportArtifact.id,
                    )
                )
            ),
            ~exists(
                select(CalcExecutionBundleComponent.id).where(
                    or_(
                        CalcExecutionBundleComponent.sourceArtifactId
                        == CalcReportArtifact.id,
                        CalcExecutionBundleComponent.executionArtifactId
                        == CalcReportArtifact.id,
                    )
                )
            ),
            ~exists(
                select(CalcReportArtifactBuild.id).where(
                    or_(
                        CalcReportArtifactBuild.sourceArtifactId
                        == CalcReportArtifact.id,
                        CalcReportArtifactBuild.outputArtifactId
                        == CalcReportArtifact.id,
                    )
                )
            ),
        )
    )
    await session.commit()
    return (
        bundle_result.rowcount or 0,
        build_result.rowcount or 0,
        artifact_result.rowcount or 0,
    )


def _remove_orphan_hash_directories(root: Path, tracked_hashes: set[str]) -> int:
    """Remove old content-hash directories absent from a tracked hash set.

    Args:
        root: Cache ``sha256`` directory containing prefix/hash directories.
        tracked_hashes: Hashes that remain authoritative in the database.

    Returns:
        Number of directories removed.

    Raises:
        None. Individual filesystem failures leave the affected cache intact.
    """
    if not root.is_dir():
        return 0
    cutoff = datetime.datetime.now(datetime.timezone.utc).timestamp() - int(
        _ORPHAN_GRACE_PERIOD.total_seconds()
    )
    removed = 0
    for prefix in root.iterdir():
        if not prefix.is_dir():
            continue
        for candidate in prefix.iterdir():
            try:
                if (
                    not candidate.is_dir()
                    or candidate.name in tracked_hashes
                    or candidate.stat().st_mtime >= cutoff
                ):
                    continue
                shutil.rmtree(candidate, onerror=_make_removable)
                removed += 1
            except OSError:
                logging.getLogger("apscheduler").exception(
                    "Failed to remove orphaned calculation cache %s", candidate
                )
        try:
            prefix.rmdir()
        except OSError:
            pass
    return removed


def _make_removable(function, path: str, _error_info) -> None:
    """Make a read-only cache path writable and retry its failed deletion."""
    Path(path).chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    function(path)
