"""On-demand pre-instrumentation builds coordinated by database leases."""

from __future__ import annotations

import asyncio
import datetime
import importlib.metadata
import platform
import uuid
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_state import BuildStatus
from app.sandbox.core.backend_types import SandboxBackendMode, configured_backend_mode
from app.db.models.calc_report_artifact import (
    CalcReportArtifact,
    CalcReportArtifactBuild,
)
from app.db.models.enums import ArtifactBuildStatus, ArtifactKind
from app.exception.custom_exception import CustomException, raise_ex
from app.service.calc_report_artifact_service import (
    ArtifactFile,
    ArtifactStore,
    PublishedArtifact,
    artifact_store,
)
from config import app_config, logger
from uzoncalc.handcalc.preinstrument import (
    INSTRUMENTATION_FORMAT_VERSION,
    preinstrument_source,
)
from uzoncalc.workspace_imports import workspace_import_roots

_LEASE_SECONDS = 180
_POLL_INTERVAL_SECONDS = 0.1
_BUILD_POOL: ProcessPoolExecutor | None = None


def local_runtime_fingerprint() -> str:
    """Return the deterministic local runtime/toolchain fingerprint."""
    try:
        package_version = importlib.metadata.version("uzoncalc")
    except importlib.metadata.PackageNotFoundError:
        package_version = "source"
    return ":".join(
        [
            f"uzoncalc-{package_version}",
            f"instrumentation-{INSTRUMENTATION_FORMAT_VERSION}",
            platform.python_implementation().lower(),
            f"py-{platform.python_version_tuple()[0]}.{platform.python_version_tuple()[1]}",
            f"api-{app_config.version}",
        ]
    )


def configured_runtime_fingerprint_hint() -> str | None:
    """Return the exact configured fingerprint when no remote probe is needed.

    Returns:
        Local fingerprint, pinned Docker fingerprint, or ``None`` when the
        remote service must report its current image digest.
    """
    mode = configured_backend_mode(app_config.sandbox_mode)
    if mode is not SandboxBackendMode.DOCKER:
        return local_runtime_fingerprint()
    image_digest = app_config.sandbox_runtime_image_digest
    return (
        f"docker:{image_digest}:instrumentation-{INSTRUMENTATION_FORMAT_VERSION}"
        if image_digest
        else None
    )


async def ensure_instrumented_artifact(
    source_artifact_id: int,
    runtime_fingerprint: str,
    session: AsyncSession,
) -> CalcReportArtifact:
    """Return a READY execution artifact, lazily building it once.

    Args:
        source_artifact_id: SOURCE artifact database ID.
        runtime_fingerprint: Exact target runtime/toolchain identity.
        session: Database session.

    Returns:
        READY INSTRUMENTED artifact.

    Raises:
        CustomException: If the build fails or exceeds the configured wait time.
    """
    source_artifact = await session.get(CalcReportArtifact, source_artifact_id)
    if (
        source_artifact is None
        or source_artifact.artifactKind != ArtifactKind.SOURCE.value
    ):
        raise_ex("SOURCE artifact not found", code=500)
    build = await _get_or_create_build(source_artifact_id, runtime_fingerprint, session)
    if build.status == ArtifactBuildStatus.READY.value:
        return await _get_ready_output(build, session)
    if build.status == ArtifactBuildStatus.FAILED.value:
        _raise_build_failed(build)

    lease_owner = uuid.uuid4().hex
    now = datetime.datetime.now(datetime.timezone.utc)
    claim = await session.execute(
        update(CalcReportArtifactBuild)
        .where(
            CalcReportArtifactBuild.id == build.id,
            or_(
                CalcReportArtifactBuild.status == ArtifactBuildStatus.PENDING.value,
                (CalcReportArtifactBuild.status == ArtifactBuildStatus.BUILDING.value)
                & (CalcReportArtifactBuild.leaseExpiresAt < now),
            ),
        )
        .values(
            status=ArtifactBuildStatus.BUILDING.value,
            leaseOwner=lease_owner,
            leaseExpiresAt=now + datetime.timedelta(seconds=_LEASE_SECONDS),
            startedAt=now,
            completedAt=None,
            diagnostics=None,
            attemptCount=CalcReportArtifactBuild.attemptCount + 1,
        )
    )
    await session.commit()
    if claim.rowcount == 1:
        return await _run_claimed_build(
            source_artifact,
            build.id,
            lease_owner,
            runtime_fingerprint,
            session,
        )
    return await _wait_for_build(build.id, session)


async def get_build_state(
    source_artifact_id: int,
    runtime_fingerprint: str,
    session: AsyncSession,
) -> tuple[BuildStatus, dict | None]:
    """Return selected-runtime build state without creating a task."""
    build = await session.scalar(
        select(CalcReportArtifactBuild).where(
            CalcReportArtifactBuild.sourceArtifactId == source_artifact_id,
            CalcReportArtifactBuild.runtimeFingerprint == runtime_fingerprint,
        )
    )
    if build is None:
        return BuildStatus.NOT_REQUESTED, None
    status = ArtifactBuildStatus(build.status)
    return BuildStatus[status.name], build.diagnostics


async def _get_or_create_build(
    source_artifact_id: int,
    runtime_fingerprint: str,
    session: AsyncSession,
) -> CalcReportArtifactBuild:
    """Get or create the unique source/runtime build row."""
    build = await session.scalar(
        select(CalcReportArtifactBuild).where(
            CalcReportArtifactBuild.sourceArtifactId == source_artifact_id,
            CalcReportArtifactBuild.runtimeFingerprint == runtime_fingerprint,
        )
    )
    if build is None:
        try:
            async with session.begin_nested():
                build = CalcReportArtifactBuild(
                    sourceArtifactId=source_artifact_id,
                    runtimeFingerprint=runtime_fingerprint,
                    status=ArtifactBuildStatus.PENDING.value,
                )
                session.add(build)
                await session.flush()
        except IntegrityError:
            build = await session.scalar(
                select(CalcReportArtifactBuild).where(
                    CalcReportArtifactBuild.sourceArtifactId == source_artifact_id,
                    CalcReportArtifactBuild.runtimeFingerprint == runtime_fingerprint,
                )
            )
            if build is None:
                raise
        await session.commit()
        await session.refresh(build)
    return build


async def _run_claimed_build(
    source_artifact: CalcReportArtifact,
    build_id: int,
    lease_owner: str,
    runtime_fingerprint: str,
    session: AsyncSession,
) -> CalcReportArtifact:
    """Run one claimed pure-AST build and atomically publish its result."""
    try:
        loop = asyncio.get_running_loop()
        published = await asyncio.wait_for(
            loop.run_in_executor(
                _get_build_pool(),
                partial(
                    _build_instrumented_sync,
                    str(artifact_store.root.resolve()),
                    source_artifact.storageKey,
                    source_artifact.contentHash,
                    runtime_fingerprint,
                    source_artifact.manifest,
                ),
            ),
            timeout=app_config.calc_report_build_wait_timeout,
        )
        output = await session.scalar(
            select(CalcReportArtifact).where(
                CalcReportArtifact.contentHash == published.content_hash
            )
        )
        if output is None:
            output = CalcReportArtifact(
                artifactKind=ArtifactKind.INSTRUMENTED.value,
                contentHash=published.content_hash,
                storageKey=published.storage_key,
                manifest=published.manifest,
                fileCount=published.file_count,
                totalSize=published.total_size,
                formatVersion=1,
            )
            session.add(output)
            await session.flush()
        completed_at = datetime.datetime.now(datetime.timezone.utc)
        result = await session.execute(
            update(CalcReportArtifactBuild)
            .where(
                CalcReportArtifactBuild.id == build_id,
                CalcReportArtifactBuild.leaseOwner == lease_owner,
            )
            .values(
                outputArtifactId=output.id,
                status=ArtifactBuildStatus.READY.value,
                diagnostics=None,
                leaseOwner=None,
                leaseExpiresAt=None,
                completedAt=completed_at,
            )
        )
        if result.rowcount != 1:
            await session.rollback()
            return await _wait_for_build(build_id, session)
        await session.commit()
        return output
    except CustomException:
        raise
    except Exception as error:
        logger.exception("Pre-instrumentation build failed for %s", source_artifact.oid)
        await session.rollback()
        diagnostics = {
            "type": type(error).__name__,
            "message": str(error),
        }
        await session.execute(
            update(CalcReportArtifactBuild)
            .where(
                CalcReportArtifactBuild.id == build_id,
                CalcReportArtifactBuild.leaseOwner == lease_owner,
            )
            .values(
                status=ArtifactBuildStatus.FAILED.value,
                diagnostics=diagnostics,
                leaseOwner=None,
                leaseExpiresAt=None,
                completedAt=datetime.datetime.now(datetime.timezone.utc),
            )
        )
        await session.commit()
        raise_ex(
            "Execution artifact build failed",
            code=422,
            data={"diagnostics": diagnostics},
            error_code=CalcErrorCode.EXECUTION_ARTIFACT_BUILD_FAILED,
        )


async def _wait_for_build(build_id: int, session: AsyncSession) -> CalcReportArtifact:
    """Wait for a concurrently claimed build to reach a terminal state."""
    deadline = (
        asyncio.get_running_loop().time() + app_config.calc_report_build_wait_timeout
    )
    while asyncio.get_running_loop().time() < deadline:
        session.expire_all()
        build = await session.get(CalcReportArtifactBuild, build_id)
        if build is not None and build.status == ArtifactBuildStatus.READY.value:
            return await _get_ready_output(build, session)
        if build is not None and build.status == ArtifactBuildStatus.FAILED.value:
            _raise_build_failed(build)
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
    raise_ex(
        "Execution artifact is not ready",
        code=409,
        data={"retryAfter": 1},
        error_code=CalcErrorCode.EXECUTION_ARTIFACT_NOT_READY,
    )


async def _get_ready_output(
    build: CalcReportArtifactBuild, session: AsyncSession
) -> CalcReportArtifact:
    """Load and validate the output referenced by a READY build."""
    if build.outputArtifactId is None:
        raise_ex("READY build has no output artifact", code=500)
    output = await session.get(CalcReportArtifact, build.outputArtifactId)
    if output is None or output.artifactKind != ArtifactKind.INSTRUMENTED.value:
        raise_ex("Execution artifact not found", code=500)
    return output


def _raise_build_failed(build: CalcReportArtifactBuild) -> None:
    """Raise the stable structured error for a failed build."""
    raise_ex(
        "Execution artifact build failed",
        code=422,
        data={"diagnostics": build.diagnostics or {}},
        error_code=CalcErrorCode.EXECUTION_ARTIFACT_BUILD_FAILED,
    )


def _get_build_pool() -> ProcessPoolExecutor:
    """Lazily create the bounded pure-AST helper process pool."""
    global _BUILD_POOL
    if _BUILD_POOL is None:
        _BUILD_POOL = ProcessPoolExecutor(max_workers=2)
    return _BUILD_POOL


def _build_instrumented_sync(
    artifact_root: str,
    source_storage_key: str,
    source_hash: str,
    runtime_fingerprint: str,
    source_manifest: dict,
) -> PublishedArtifact:
    """Build and publish one execution artifact inside a helper process.

    Args:
        artifact_root: Root directory of the content-addressed artifact store.
        source_storage_key: Storage key of the source artifact to transform.
        source_hash: Stable content hash of the source artifact.
        runtime_fingerprint: Runtime identity associated with the build output.
        source_manifest: Validated source manifest containing files and dependencies.

    Returns:
        Published instrumented artifact metadata.

    Raises:
        OSError: If source artifacts cannot be read or outputs cannot be published.
        UnicodeDecodeError: If a Python source file is not valid UTF-8.
        SyntaxError: If a Python source file cannot be parsed or transformed.
        ValueError: If an import or dependency declaration cannot be normalized.
    """
    store = ArtifactStore(Path(artifact_root))
    defaults = {
        dependency["alias"]: next(
            selector["selectorKey"]
            for selector in dependency["selectors"]
            if selector["isDefault"]
        )
        for dependency in source_manifest.get("dependencies", [])
    }
    scope_key = f"scope_{source_hash[:16]}"
    import_roots = workspace_import_roots(
        file_entry["path"] for file_entry in source_manifest.get("files", [])
    )
    output_files: list[ArtifactFile] = []
    source_maps: dict[str, list[dict]] = {}
    for source_file in store.read_all(source_storage_key):
        if not source_file.path.endswith(".py"):
            continue
        result = preinstrument_source(
            source_file.content.decode("utf-8"),
            filename=source_file.path,
            scope_key=scope_key,
            dependency_defaults=defaults,
            workspace_import_roots=import_roots,
        )
        output_files.append(
            ArtifactFile(source_file.path, result.source.encode("utf-8"))
        )
        source_maps[source_file.path] = result.source_map
    return store.publish_instrumented(
        output_files,
        source_hash=source_hash,
        runtime_fingerprint=runtime_fingerprint,
        source_maps=source_maps,
    )
