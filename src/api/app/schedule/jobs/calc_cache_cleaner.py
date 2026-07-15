"""Scheduled cleanup for orphaned calculation artifact and bundle caches."""

import datetime
import logging
import shutil
import stat
from pathlib import Path

from sqlalchemy import select

from app.db.manager import get_db_manager
from app.db.models.calc_execution import CalcExecutionBundle
from app.db.models.calc_report_artifact import CalcReportArtifact
from app.schedule.cron_schedule_job import BaseCronScheduleJob
from config import app_config

_ORPHAN_GRACE_PERIOD = datetime.timedelta(hours=24)


class CalcCacheCleanerScheduleJob(BaseCronScheduleJob):
    """Remove old cache directories that have no corresponding database row."""

    def __init__(self) -> None:
        """Configure the calculation-cache cleanup to run daily at 03:20 UTC."""
        super().__init__("calc_cache_cleaner_schedule_job", "0 20 3 * * *")

    async def run_async(self) -> None:
        """Load tracked hashes and remove only sufficiently old disk orphans."""
        logger = logging.getLogger("apscheduler")
        async with get_db_manager().session() as session:
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
            "Calculation cache cleanup completed - artifacts: %s, bundles: %s",
            removed_artifacts,
            removed_bundles,
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
