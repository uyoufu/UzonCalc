"""HTTP endpoints for reproducible managed calculation execution."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_execution_dto import (
    CalcExecutionContinueDTO,
    CalcExecutionResDTO,
    CalcExecutionStartDTO,
)
from app.controller.calc.calc_state import (
    ExecutionSourceType,
    ExecutionStatus,
    ExecutorType,
)
from app.controller.depends import get_session, get_token_payload
from app.db.models.enums import (
    ExecutionSourceType as DbExecutionSourceType,
    ExecutionStatus as DbExecutionStatus,
    ExecutorType as DbExecutorType,
)
from app.db.models.calc_report_instance import CalcReportInstance
from app.response.response_result import ResponseResult, ok
from app.sandbox.core.backend_types import SandboxBackendMode
from app.sandbox.core.execution_result import ExecutionResult
from app.service import calc_execution_service
from app.service.calc_execution_service import ExecutionStep
from app.service.html_cache.html_cacher import html_cacher
from utils.jwt_helper import TokenPayloads

router = APIRouter(prefix="/v1/calc/execution", tags=["calc-execution"])


@router.post("")
async def start_calc_execution(
    request: CalcExecutionStartDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcExecutionResDTO]:
    """Start one workspace/latest/version execution."""
    step = await calc_execution_service.start_execution(
        session, tokenPayloads.id, request
    )
    response = await finalize_execution_step(
        step, request.lastHtmlPath, tokenPayloads.id, session
    )
    return ok(data=response)


@router.get("/current")
async def get_current_calc_execution(
    reportOid: str,
    sourceType: ExecutionSourceType = ExecutionSourceType.WORKSPACE,
    versionName: str | None = None,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcExecutionResDTO | None]:
    """Return the active or last-successful execution for one report target."""
    step = await calc_execution_service.get_current_execution_step(
        session,
        tokenPayloads.id,
        CalcExecutionStartDTO(
            reportOid=reportOid,
            source={"type": sourceType, "versionName": versionName},
        ),
    )
    return ok(data=execution_step_response(step) if step is not None else None)


@router.post("/{executionId}/continue")
async def continue_calc_execution(
    executionId: str,
    request: CalcExecutionContinueDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcExecutionResDTO]:
    """Continue the original process/container without rebuilding its bundle."""
    step = await calc_execution_service.continue_execution(
        session, tokenPayloads.id, executionId, request.defaults
    )
    response = await finalize_execution_step(
        step, request.lastHtmlPath, tokenPayloads.id, session
    )
    return ok(data=response)


@router.get("/{executionId}")
async def get_calc_execution(
    executionId: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcExecutionResDTO]:
    """Return one persisted execution and immutable provenance."""
    step = await calc_execution_service.get_execution_step(
        session, tokenPayloads.id, executionId
    )
    return ok(data=execution_step_response(step))


@router.delete("/{executionId}")
async def terminate_calc_execution(
    executionId: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """Terminate an active execution idempotently."""
    await calc_execution_service.terminate_execution(
        session, tokenPayloads.id, executionId
    )
    return ok()


async def finalize_execution_step(
    step: ExecutionStep,
    last_html_path: str | None,
    user_id: int,
    session: AsyncSession,
) -> CalcExecutionResDTO:
    """Cache internal HTML, persist its path, and build the public response."""
    public_result = ExecutionResult.model_validate(step.result)
    public_result.executionId = step.execution.oid
    html_path = await html_cacher.cache_html(public_result, user_id, session)
    patch = html_cacher.build_content_patch_from_paths(last_html_path, html_path)
    await calc_execution_service.record_result_path(
        session, step.execution.oid, user_id, html_path
    )
    if step.result.isCompleted:
        slot = await calc_execution_service.promote_successful_execution(
            session, step.execution.oid, user_id
        )
        if slot is not None and slot.instanceId is not None:
            instance = await session.get(CalcReportInstance, slot.instanceId)
            if instance is not None:
                from app.service.calc_report_instance_service import (
                    apply_instance_execution_result,
                )

                await apply_instance_execution_result(
                    user_id, instance.oid, step.execution.oid, session
                )
    response = execution_step_response(step)
    response.htmlPath = html_path
    response.updateType = patch.updateType
    response.htmlContentPatch = patch.contentHtml
    return response


def execution_step_response(step: ExecutionStep) -> CalcExecutionResDTO:
    """Convert internal execution models into a stable public response."""
    resolved_version = (
        f"{step.resolved_version.major}.{step.resolved_version.minor}."
        f"{step.resolved_version.patch}"
        if step.resolved_version is not None
        else None
    )
    return CalcExecutionResDTO(
        executionId=step.execution.oid,
        reportOid=step.report.oid,
        sourceType=ExecutionSourceType[
            DbExecutionSourceType(step.execution.sourceType).name
        ],
        resolvedVersion=resolved_version,
        sourceArtifactHash=f"sha256:{step.source_artifact.contentHash}",
        executionArtifactHash=f"sha256:{step.execution_artifact.contentHash}",
        bundleHash=f"sha256:{step.bundle.bundleHash}",
        runtimeFingerprint=step.bundle.runtimeFingerprint,
        executorType=ExecutorType[DbExecutorType(step.execution.executorType).name],
        backendMode=SandboxBackendMode(
            (step.execution.metrics or {}).get("backend", step.runtime.mode)
        ),
        status=ExecutionStatus[DbExecutionStatus(step.execution.status).name],
        isCompleted=step.result.isCompleted,
        windows=step.result.windows,
        htmlPath=step.execution.resultPath or "",
        createdAt=step.execution.createdAt,
        completedAt=step.execution.completedAt,
    )
