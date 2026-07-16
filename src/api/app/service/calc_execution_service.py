"""Reproducible execution orchestration and interaction-state persistence."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_execution_dto import CalcExecutionStartDTO
from app.controller.dto_base import PaginationDTO
from app.db.models.calc_execution import CalcExecution, CalcExecutionBundle
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_artifact import CalcReportArtifact
from app.db.models.calc_report_version import CalcReportVersion
from app.db.models.enums import ExecutionSourceType, ExecutionStatus, ExecutorType
from app.db.models.user_input_history import InputCache, UserInputHistory
from app.exception.custom_exception import raise_ex
from app.sandbox.core.backend_factory import get_sandbox_executor
from app.sandbox.core.backend_types import RuntimeDescriptor
from app.sandbox.core.execution_result import ExecutionResult
from app.service.calc_execution_bundle_service import (
    ResolvedExecutionSource,
    prepare_execution_bundle,
    resolve_execution_source,
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
    source = await resolve_execution_source(
        user_id,
        request.reportOid,
        request.source.type,
        request.source.versionName,
        session,
    )
    bundle, prepared = await prepare_execution_bundle(user_id, source, runtime, session)
    execution_artifact = await session.get(
        CalcReportArtifact, bundle.entryExecutionArtifactId
    )
    if execution_artifact is None:
        raise_ex("Bundle execution artifact not found", code=500)
    defaults = await _merge_cached_defaults(
        user_id,
        source.report,
        source.source_artifact,
        request.defaults,
        session,
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
    history = UserInputHistory(
        executionId=execution.id,
        defaults=defaults,
        inputHistory=[{"step": 0, "defaults": defaults}],
        currentStep=0,
        totalSteps=0,
    )
    session.add(history)
    await session.commit()
    try:
        result = await executor.execute_bundle(
            prepared, defaults, is_silent=request.isSilent
        )
    except Exception as error:
        await _mark_execution_failed(execution, error, session)
        raise
    await _apply_backend_result(execution, history, result, source, session, defaults)
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
    execution.status = ExecutionStatus.CANCELLED.value
    execution.completedAt = datetime.datetime.now(datetime.timezone.utc)
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
    backend_name = (execution.metrics or {}).get("backend", "in_process")
    from app.sandbox.core.backend_types import SandboxBackendMode

    runtime = RuntimeDescriptor(
        mode=SandboxBackendMode(backend_name),
        fingerprint=bundle.runtimeFingerprint,
        executor_type=ExecutorType(execution.executorType),
        image_digest=bundle.runtimeImageDigest,
        node_id=execution.executorNodeId,
    )
    return ExecutionStep(
        execution=execution,
        result=ExecutionResult(
            executionId=execution.oid,
            html="",
            isCompleted=execution.status != ExecutionStatus.RUNNING.value,
            windows=[],
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


async def count_executions(session: AsyncSession, user_id: int) -> int:
    """Count persisted execution audits owned by one user."""
    total = await session.scalar(
        select(func.count(CalcExecution.id)).where(CalcExecution.userId == user_id)
    )
    return total or 0


async def list_execution_oids(
    session: AsyncSession,
    user_id: int,
    pagination: PaginationDTO,
) -> list[str]:
    """List one sorted page of execution audit OIDs."""
    sort_columns = {
        "id": CalcExecution.id,
        "createdAt": CalcExecution.createdAt,
        "status": CalcExecution.status,
        "sourceType": CalcExecution.sourceType,
    }
    sort_column = sort_columns.get(pagination.sortBy, CalcExecution.createdAt)
    sort_expression = sort_column.desc() if pagination.descending else sort_column.asc()
    stable_sort = (
        CalcExecution.id.desc() if pagination.descending else CalcExecution.id.asc()
    )
    oids = (
        await session.scalars(
            select(CalcExecution.oid)
            .where(CalcExecution.userId == user_id)
            .order_by(sort_expression, stable_sort)
            .offset(pagination.skip)
            .limit(pagination.limit)
        )
    ).all()
    return list(oids)


async def expire_orphaned_executions(session: AsyncSession) -> int:
    """Mark startup-surviving PENDING/RUNNING rows as process-lost failures."""
    executions = (
        await session.scalars(
            select(CalcExecution).where(
                CalcExecution.status.in_(
                    [ExecutionStatus.PENDING.value, ExecutionStatus.RUNNING.value]
                )
            )
        )
    ).all()
    now = datetime.datetime.now(datetime.timezone.utc)
    for execution in executions:
        execution.status = ExecutionStatus.FAILED.value
        execution.errorCode = CalcErrorCode.EXECUTION_PROCESS_LOST.value
        execution.errorMessage = "API process restarted while execution was active"
        execution.completedAt = now
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
    if cache is not None and cache.sourceArtifactId == source_artifact.id:
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
    history.inputHistory = [
        *(history.inputHistory or []),
        {"step": history.currentStep + 1, "defaults": submitted_defaults},
    ]
    history.currentStep += 1
    history.totalSteps = max(history.totalSteps, history.currentStep)
    flag_modified(history, "defaults")
    flag_modified(history, "inputHistory")
    extracted = _extract_defaults_from_windows(result.windows)
    if extracted:
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
                sourceArtifactId=source.source_artifact.id,
                defaults=extracted,
            )
            session.add(cache)
        else:
            cache.sourceArtifactId = source.source_artifact.id
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
    execution.status = ExecutionStatus.FAILED.value
    execution.errorCode = (
        CalcErrorCode.EXECUTION_PROCESS_LOST.value
        if process_lost
        else type(error).__name__
    )
    execution.errorMessage = str(error)
    execution.completedAt = datetime.datetime.now(datetime.timezone.utc)
    await session.commit()


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
