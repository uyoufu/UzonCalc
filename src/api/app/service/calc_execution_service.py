"""Reproducible execution orchestration and interaction-state persistence."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Any, cast

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_execution_dto import CalcExecutionStartDTO
from app.controller.calc.calc_state import (
    ExecutionSourceType as ApiExecutionSourceType,
)
from app.db.models.calc_execution import (
    CalcExecution,
    CalcExecutionBundle,
    CalcExecutionSlot,
)
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_artifact import CalcReportArtifact
from app.db.models.calc_report_version import CalcReportVersion
from app.db.models.enums import (
    ExecutionSourceType,
    ExecutionStatus,
    ExecutionTargetType,
    ExecutorType,
)
from app.db.models.user_input_history import InputCache, UserInputHistory
from app.db.models.tmp_file import TmpFile
from app.exception.custom_exception import raise_ex
from app.sandbox.core.backend_factory import get_sandbox_executor
from app.sandbox.core.backend_types import RuntimeDescriptor, SandboxBackendMode
from app.sandbox.core.execution_result import ExecutionResult
from app.service.calc_execution_bundle_service import (
    ResolvedExecutionSource,
    prepare_execution_bundle,
    prepare_retained_execution_bundle,
    resolve_execution_source,
)
from app.service.calc_report_workspace_service import (
    get_owned_report,
    parse_version_name,
)
from config import app_config


@dataclass(frozen=True)
class ExecutionStep:
    """Combine one backend result with persisted provenance models."""

    execution: CalcExecution
    result: ExecutionResult
    report: CalcReport
    source_artifact: CalcReportArtifact
    execution_artifact: CalcReportArtifact
    bundle: CalcExecutionBundle
    runtime: RuntimeDescriptor
    resolved_version: CalcReportVersion | None


async def start_execution(
    session: AsyncSession,
    user_id: int,
    request: CalcExecutionStartDTO,
    *,
    use_cached_defaults: bool = True,
    persist_input_cache: bool = True,
    slot_override: CalcExecutionSlot | None = None,
    source_override: ResolvedExecutionSource | None = None,
    bundle_override: CalcExecutionBundle | None = None,
) -> ExecutionStep:
    """Resolve, lazily build, bundle, audit, and start one execution."""
    executor = get_sandbox_executor()
    try:
        runtime = await executor.runtime_descriptor()
    except Exception as error:
        raise_ex(
            "Configured sandbox backend is unavailable",
            code=503,
            data={"message": str(error)},
            error_code=CalcErrorCode.SANDBOX_BACKEND_UNAVAILABLE,
        )
    source = source_override or await resolve_execution_source(
        user_id,
        request.reportOid,
        request.source.type,
        request.source.versionName,
        session,
    )
    if bundle_override is not None:
        if bundle_override.runtimeFingerprint != runtime.fingerprint:
            raise_ex(
                "Retained instance runtime is unavailable in the configured backend",
                code=409,
            )
        bundle = bundle_override
        prepared = await prepare_retained_execution_bundle(
            bundle_override, source.report, session
        )
    else:
        bundle, prepared = await prepare_execution_bundle(
            user_id, source, runtime, session
        )
    slot = slot_override or await _get_or_create_report_execution_slot(
        user_id, source, session
    )
    if slot.id is not None:
        locked_slot = await session.get(
            CalcExecutionSlot, slot.id, with_for_update=True
        )
        if locked_slot is not None:
            slot = locked_slot
    if slot.activeExecutionId is not None:
        raise_ex("An execution is already active for this target", code=409)
    execution_artifact = await session.get(
        CalcReportArtifact, bundle.entryExecutionArtifactId
    )
    if execution_artifact is None:
        raise_ex("Bundle execution artifact not found", code=500)
    defaults = (
        await _merge_cached_defaults(
            user_id,
            source.report,
            source.source_artifact,
            request.defaults,
            session,
        )
        if use_cached_defaults
        else request.defaults
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    execution = CalcExecution(
        userId=user_id,
        reportId=source.report.id,
        bundleId=bundle.id,
        sourceType=source.source_type.value,
        resolvedVersionId=(
            source.resolved_version.id if source.resolved_version is not None else None
        ),
        executorType=runtime.executor_type.value,
        status=ExecutionStatus.PENDING.value,
        executorNodeId=runtime.node_id,
        expiresAt=now + datetime.timedelta(seconds=app_config.sandbox_session_timeout),
        metrics={"backend": runtime.mode.value},
    )
    session.add(execution)
    await session.flush()
    slot.activeExecutionId = execution.id
    history = UserInputHistory(executionId=execution.id, defaults=defaults)
    session.add(history)
    await session.commit()
    try:
        result = await executor.execute_bundle(
            prepared, defaults, is_silent=request.isSilent
        )
    except Exception as error:
        await _mark_execution_failed(execution, error, session)
        raise
    await _apply_backend_result(
        execution,
        history,
        result,
        source,
        session,
        defaults,
        persist_input_cache=persist_input_cache,
    )
    return ExecutionStep(
        execution=execution,
        result=result,
        report=source.report,
        source_artifact=source.source_artifact,
        execution_artifact=execution_artifact,
        bundle=bundle,
        runtime=runtime,
        resolved_version=source.resolved_version,
    )


async def continue_execution(
    session: AsyncSession,
    user_id: int,
    execution_oid: str,
    defaults: dict[str, dict[str, Any]],
) -> ExecutionStep:
    """Continue the original backend session without rebuilding or resolving latest."""
    execution = await _get_execution(user_id, execution_oid, session)
    if (
        execution.status != ExecutionStatus.RUNNING.value
        or not execution.sandboxExecutionId
    ):
        raise_ex(
            "Execution session is no longer active",
            code=410,
            error_code=CalcErrorCode.EXECUTION_PROCESS_LOST,
        )
    executor = get_sandbox_executor()
    runtime = await executor.runtime_descriptor()
    try:
        result = await executor.continue_execution(
            execution.sandboxExecutionId, defaults
        )
    except (ValueError, KeyError) as error:
        await _mark_execution_failed(execution, error, session, process_lost=True)
        raise_ex(
            "Execution process was lost",
            code=410,
            error_code=CalcErrorCode.EXECUTION_PROCESS_LOST,
        )
    history = await session.scalar(
        select(UserInputHistory).where(UserInputHistory.executionId == execution.id)
    )
    if history is None:
        raise_ex("Execution input history not found", code=500)
    report = await session.get(CalcReport, execution.reportId)
    bundle = await session.get(CalcExecutionBundle, execution.bundleId)
    if report is None or bundle is None:
        raise_ex("Execution provenance is incomplete", code=500)
    source_artifact = await session.get(
        CalcReportArtifact, bundle.entrySourceArtifactId
    )
    execution_artifact = await session.get(
        CalcReportArtifact, bundle.entryExecutionArtifactId
    )
    if source_artifact is None or execution_artifact is None:
        raise_ex("Execution artifacts not found", code=500)
    source = ResolvedExecutionSource(
        report=report,
        source_artifact=source_artifact,
        source_type=ExecutionSourceType(execution.sourceType),
        resolved_version=(
            await session.get(CalcReportVersion, execution.resolvedVersionId)
            if execution.resolvedVersionId is not None
            else None
        ),
    )
    await _apply_backend_result(execution, history, result, source, session, defaults)
    return ExecutionStep(
        execution=execution,
        result=result,
        report=report,
        source_artifact=source_artifact,
        execution_artifact=execution_artifact,
        bundle=bundle,
        runtime=runtime,
        resolved_version=source.resolved_version,
    )


async def terminate_execution(
    session: AsyncSession, user_id: int, execution_oid: str
) -> None:
    """Terminate an active backend session and persist CANCELLED."""
    execution = await _get_execution(user_id, execution_oid, session)
    if execution.sandboxExecutionId:
        await get_sandbox_executor().terminate(execution.sandboxExecutionId)
    slot = await _slot_for_execution(execution.id, session)
    if slot is not None and slot.activeExecutionId == execution.id:
        slot.activeExecutionId = None
    _remove_execution_result(execution.resultPath)
    await session.delete(execution)
    await session.commit()


async def record_result_path(
    session: AsyncSession,
    execution_oid: str,
    user_id: int,
    result_path: str,
) -> None:
    """Attach a cached public HTML path to an owned execution audit row."""
    execution = await _get_execution(user_id, execution_oid, session)
    execution.resultPath = result_path
    await session.commit()


async def promote_successful_execution(
    session: AsyncSession,
    execution_oid: str,
    user_id: int,
) -> CalcExecutionSlot | None:
    """Promote one completed active execution and delete the previous success."""
    execution = await _get_execution(user_id, execution_oid, session)
    if execution.status != ExecutionStatus.SUCCEEDED.value or not execution.resultPath:
        return None
    slot = await _slot_for_execution(execution.id, session)
    if slot is None or slot.activeExecutionId != execution.id:
        raise_ex("Execution target is no longer active", code=409)
    previous_id = slot.currentExecutionId
    slot.currentExecutionId = execution.id
    slot.activeExecutionId = None
    result_file = Path("data") / execution.resultPath
    await session.execute(
        delete(TmpFile).where(TmpFile.filePath == str(result_file.parent))
    )
    previous = (
        await session.get(CalcExecution, previous_id)
        if previous_id is not None and previous_id != execution.id
        else None
    )
    if previous is not None:
        _remove_execution_result(previous.resultPath)
        await session.delete(previous)
    await session.commit()
    return slot


async def get_current_execution_step(
    session: AsyncSession,
    user_id: int,
    request: CalcExecutionStartDTO,
) -> ExecutionStep | None:
    """Return the active execution or retained success for one report source."""
    report = await get_owned_report(user_id, request.reportOid, session)
    version: CalcReportVersion | None = None
    if request.source.type is ApiExecutionSourceType.LATEST:
        version = (
            await session.get(CalcReportVersion, report.latestVersionId)
            if report.latestVersionId is not None
            else None
        )
    elif request.source.type is ApiExecutionSourceType.VERSION:
        if not request.source.versionName:
            raise_ex("versionName is required for version execution", code=400)
        try:
            major, minor, patch = parse_version_name(request.source.versionName)
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
    if request.source.type is not ApiExecutionSourceType.WORKSPACE and version is None:
        return None
    slot = await _find_report_execution_slot(user_id, report.id, version, session)
    if slot is None:
        return None
    execution_id = slot.activeExecutionId or slot.currentExecutionId
    if execution_id is None:
        return None
    execution = await session.get(CalcExecution, execution_id)
    return (
        await get_execution_step(session, user_id, execution.oid)
        if execution is not None
        else None
    )


async def get_execution_step(
    session: AsyncSession, user_id: int, execution_oid: str
) -> ExecutionStep:
    """Load persisted provenance for a detail/history response without windows."""
    execution = await _get_execution(user_id, execution_oid, session)
    report = await session.get(CalcReport, execution.reportId)
    bundle = await session.get(CalcExecutionBundle, execution.bundleId)
    if report is None or bundle is None:
        raise_ex("Execution provenance is incomplete", code=500)
    source_artifact = await session.get(
        CalcReportArtifact, bundle.entrySourceArtifactId
    )
    execution_artifact = await session.get(
        CalcReportArtifact, bundle.entryExecutionArtifactId
    )
    if source_artifact is None or execution_artifact is None:
        raise_ex("Execution artifacts not found", code=500)
    backend_name = (execution.metrics or {}).get(
        "backend", SandboxBackendMode.IN_PROCESS
    )

    runtime = RuntimeDescriptor(
        mode=SandboxBackendMode(backend_name),
        fingerprint=bundle.runtimeFingerprint,
        executor_type=ExecutorType(execution.executorType),
        image_digest=bundle.runtimeImageDigest,
        node_id=execution.executorNodeId,
    )
    history = await session.scalar(
        select(UserInputHistory).where(UserInputHistory.executionId == execution.id)
    )
    return ExecutionStep(
        execution=execution,
        result=ExecutionResult(
            executionId=execution.oid,
            html="",
            isCompleted=execution.status != ExecutionStatus.RUNNING.value,
            windows=history.windows if history is not None else [],
        ),
        report=report,
        source_artifact=source_artifact,
        execution_artifact=execution_artifact,
        bundle=bundle,
        runtime=runtime,
        resolved_version=(
            await session.get(CalcReportVersion, execution.resolvedVersionId)
            if execution.resolvedVersionId is not None
            else None
        ),
    )


async def expire_orphaned_executions(session: AsyncSession) -> int:
    """Delete startup-surviving active rows while preserving retained successes."""
    executions = (
        await session.scalars(
            select(CalcExecution).where(
                CalcExecution.status.in_(
                    [ExecutionStatus.PENDING.value, ExecutionStatus.RUNNING.value]
                )
            )
        )
    ).all()
    for execution in executions:
        slot = await _slot_for_execution(execution.id, session)
        if slot is not None and slot.activeExecutionId == execution.id:
            slot.activeExecutionId = None
        _remove_execution_result(execution.resultPath)
        await session.delete(execution)
    await session.commit()
    return len(executions)


async def _get_execution(
    user_id: int, execution_oid: str, session: AsyncSession
) -> CalcExecution:
    """Load one owned execution audit row by public OID."""
    execution = await session.scalar(
        select(CalcExecution).where(
            CalcExecution.oid == execution_oid,
            CalcExecution.userId == user_id,
        )
    )
    if execution is None:
        raise_ex(
            "Execution not found",
            code=404,
            error_code=CalcErrorCode.EXECUTION_NOT_FOUND,
        )
    return cast(CalcExecution, execution)


async def _merge_cached_defaults(
    user_id: int,
    report: CalcReport,
    source_artifact: CalcReportArtifact,
    requested: dict[str, dict[str, Any]],
    session: AsyncSession,
) -> dict[str, dict[str, Any]]:
    """Merge recent inputs only when they came from the same SOURCE shape."""
    cache = await session.scalar(
        select(InputCache).where(
            InputCache.userId == user_id,
            InputCache.reportId == report.id,
            InputCache.entryName == report.entryPath,
        )
    )
    merged: dict[str, dict[str, Any]] = {}
    if cache is not None and cache.sourceHash == source_artifact.contentHash:
        _deep_update(merged, cache.defaults)
    _deep_update(merged, requested)
    return merged


async def _apply_backend_result(
    execution: CalcExecution,
    history: UserInputHistory,
    result: ExecutionResult,
    source: ResolvedExecutionSource,
    session: AsyncSession,
    submitted_defaults: dict[str, dict[str, Any]],
    *,
    persist_input_cache: bool = True,
) -> None:
    """Persist one interaction result and recent-input cache update."""
    now = datetime.datetime.now(datetime.timezone.utc)
    execution.sandboxExecutionId = result.executionId
    execution.startedAt = execution.startedAt or now
    execution.lastActiveAt = now
    execution.status = (
        ExecutionStatus.SUCCEEDED.value
        if result.isCompleted
        else ExecutionStatus.RUNNING.value
    )
    execution.completedAt = now if result.isCompleted else None
    history.defaults = submitted_defaults
    history.windows = result.windows
    flag_modified(history, "defaults")
    flag_modified(history, "windows")
    extracted = _extract_defaults_from_windows(result.windows)
    if extracted and persist_input_cache:
        cache = await session.scalar(
            select(InputCache).where(
                InputCache.userId == execution.userId,
                InputCache.reportId == execution.reportId,
                InputCache.entryName == source.report.entryPath,
            )
        )
        if cache is None:
            cache = InputCache(
                userId=execution.userId,
                reportId=execution.reportId,
                entryName=source.report.entryPath,
                sourceHash=source.source_artifact.contentHash,
                defaults=extracted,
            )
            session.add(cache)
        else:
            cache.sourceHash = source.source_artifact.contentHash
            cache.defaults = extracted
            flag_modified(cache, "defaults")
    await session.commit()


async def _mark_execution_failed(
    execution: CalcExecution,
    error: Exception,
    session: AsyncSession,
    *,
    process_lost: bool = False,
) -> None:
    """Persist a terminal failure before propagating an execution exception."""
    slot = await _slot_for_execution(execution.id, session)
    if slot is not None and slot.activeExecutionId == execution.id:
        slot.activeExecutionId = None
    _remove_execution_result(execution.resultPath)
    await session.delete(execution)
    await session.commit()


async def _get_or_create_report_execution_slot(
    user_id: int,
    source: ResolvedExecutionSource,
    session: AsyncSession,
) -> CalcExecutionSlot:
    """Resolve one workspace or concrete-version retained execution slot."""
    if source.resolved_version is None:
        target_type = ExecutionTargetType.WORKSPACE
        condition = CalcExecutionSlot.reportId == source.report.id
    else:
        target_type = ExecutionTargetType.VERSION
        condition = CalcExecutionSlot.versionId == source.resolved_version.id
    slot = await session.scalar(
        select(CalcExecutionSlot)
        .where(
            CalcExecutionSlot.userId == user_id,
            CalcExecutionSlot.targetType == target_type.value,
            condition,
        )
        .with_for_update()
    )
    if slot is None:
        slot = CalcExecutionSlot(
            userId=user_id,
            targetType=target_type.value,
            reportId=source.report.id
            if target_type is ExecutionTargetType.WORKSPACE
            else None,
            versionId=(
                source.resolved_version.id
                if target_type is ExecutionTargetType.VERSION
                else None
            ),
        )
        session.add(slot)
        await session.flush()
    return slot


async def _find_report_execution_slot(
    user_id: int,
    report_id: int,
    version: CalcReportVersion | None,
    session: AsyncSession,
) -> CalcExecutionSlot | None:
    """Find a report target slot without freezing or creating source content."""
    if version is None:
        target_type = ExecutionTargetType.WORKSPACE
        condition = CalcExecutionSlot.reportId == report_id
    else:
        target_type = ExecutionTargetType.VERSION
        condition = CalcExecutionSlot.versionId == version.id
    return await session.scalar(
        select(CalcExecutionSlot).where(
            CalcExecutionSlot.userId == user_id,
            CalcExecutionSlot.targetType == target_type.value,
            condition,
        )
    )


async def discard_execution_slot(
    slot: CalcExecutionSlot,
    session: AsyncSession,
) -> None:
    """Discard active and retained executions when a target changes identity."""
    execution_ids = {slot.activeExecutionId, slot.currentExecutionId} - {None}
    executions = (
        list(
            await session.scalars(
                select(CalcExecution).where(CalcExecution.id.in_(execution_ids))
            )
        )
        if execution_ids
        else []
    )
    for execution in executions:
        if execution.id == slot.activeExecutionId and execution.sandboxExecutionId:
            await get_sandbox_executor().terminate(execution.sandboxExecutionId)
        if execution.resultPath:
            result_file = Path("data") / execution.resultPath
            await session.execute(
                delete(TmpFile).where(TmpFile.filePath == str(result_file.parent))
            )
        _remove_execution_result(execution.resultPath)
    slot.activeExecutionId = None
    slot.currentExecutionId = None
    await session.flush()
    for execution in executions:
        await session.delete(execution)


async def get_or_create_share_execution_slot(
    user_id: int,
    share_link_id: int,
    session: AsyncSession,
) -> CalcExecutionSlot:
    """Return the isolated retained execution slot for one share preview."""
    slot = await session.scalar(
        select(CalcExecutionSlot).where(
            CalcExecutionSlot.userId == user_id,
            CalcExecutionSlot.targetType == ExecutionTargetType.SHARE_PREVIEW.value,
            CalcExecutionSlot.shareLinkId == share_link_id,
        )
    )
    if slot is None:
        slot = CalcExecutionSlot(
            userId=user_id,
            targetType=ExecutionTargetType.SHARE_PREVIEW.value,
            shareLinkId=share_link_id,
        )
        session.add(slot)
        await session.flush()
    return slot


async def get_or_create_instance_execution_slot(
    user_id: int,
    instance_id: int,
    session: AsyncSession,
) -> CalcExecutionSlot:
    """Return the isolated retained execution slot for one saved instance."""
    slot = await session.scalar(
        select(CalcExecutionSlot).where(
            CalcExecutionSlot.userId == user_id,
            CalcExecutionSlot.targetType == ExecutionTargetType.INSTANCE.value,
            CalcExecutionSlot.instanceId == instance_id,
        )
    )
    if slot is None:
        slot = CalcExecutionSlot(
            userId=user_id,
            targetType=ExecutionTargetType.INSTANCE.value,
            instanceId=instance_id,
        )
        session.add(slot)
        await session.flush()
    return slot


async def _slot_for_execution(
    execution_id: int,
    session: AsyncSession,
) -> CalcExecutionSlot | None:
    """Find the slot retaining or actively running one execution."""
    return await session.scalar(
        select(CalcExecutionSlot).where(
            (CalcExecutionSlot.activeExecutionId == execution_id)
            | (CalcExecutionSlot.currentExecutionId == execution_id)
        )
    )


def _remove_execution_result(result_path: str | None) -> None:
    """Remove an execution result directory when its retained row is discarded."""
    if not result_path:
        return
    relative = Path(result_path)
    if relative.is_absolute() or ".." in relative.parts:
        return
    result_file = Path("data") / relative
    if result_file.parent.is_dir():
        shutil.rmtree(result_file.parent, ignore_errors=True)


def _extract_defaults_from_windows(
    windows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Extract named field values from backend UI-window payloads."""
    defaults: dict[str, dict[str, Any]] = {}
    for window in windows:
        title = window.get("title")
        if not title:
            continue
        values = {
            field["name"]: field.get("value")
            for field in window.get("fields", [])
            if field.get("name")
        }
        if values:
            defaults[title] = values
    return defaults


def _deep_update(target: dict, source: dict) -> None:
    """Recursively merge dictionaries without mutating the source."""
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        elif isinstance(value, dict):
            nested: dict = {}
            _deep_update(nested, value)
            target[key] = nested
        else:
            target[key] = value
