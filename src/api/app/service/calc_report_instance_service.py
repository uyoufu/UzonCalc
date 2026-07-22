"""Bundle-backed saved calculation-instance services."""

import datetime
import shutil
from pathlib import Path
from typing import Any, cast

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_instance_dto import (
    CalcInstanceCreateDTO,
    CalcInstanceListFilterDTO,
    CalcInstanceResDTO,
    CalcInstanceShareResDTO,
    CalcInstanceUpdateDTO,
)
from app.controller.dto_base import PaginationDTO
from app.db.models.calc_execution import (
    CalcExecution,
    CalcExecutionBundle,
    CalcExecutionSlot,
)
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_artifact import CalcReportArtifact
from app.db.models.calc_report_instance import (
    CalcReportInstance,
    CalcReportInstanceShare,
)
from app.db.models.calc_report_instance_category import CalcReportInstanceCategory
from app.db.models.calc_report_version import CalcReportVersion
from app.db.models.object_id import ObjectId
from app.db.models.enums import ExecutionSourceType as DbExecutionSourceType
from app.db.models.user_input_history import UserInputHistory
from app.exception.custom_exception import raise_ex
from app.service.calc_report_instance_category_service import get_category
from app.service.share_token_service import (
    create_signed_share_token,
    verify_signed_share_token,
)
from app.controller.calc.calc_execution_dto import CalcExecutionStartDTO
from app.controller.calc.calc_state import ExecutionSourceType
from app.service.calc_execution_service import (
    ExecutionStep,
    discard_execution_slot,
    get_or_create_instance_execution_slot,
    get_execution_step,
    start_execution,
)
from app.service.calc_execution_bundle_service import ResolvedExecutionSource


async def create_instance(
    user_id: int,
    request: CalcInstanceCreateDTO,
    session: AsyncSession,
) -> CalcInstanceResDTO:
    """Create a saved result from an owned persisted execution."""
    execution, report, bundle, history = await _execution_source(
        user_id, request.executionId, session
    )
    category = await get_category(user_id, request.categoryOid, session)
    if not execution.resultPath:
        raise_ex("Execution has no cached result", code=409)
    instance_oid = ObjectId().to_hex()
    result_path = _persist_result(user_id, instance_oid, execution.resultPath)
    instance = CalcReportInstance(
        oid=instance_oid,
        userId=user_id,
        categoryId=category.id,
        reportId=report.id,
        sourceVersionId=execution.resolvedVersionId,
        bundleId=bundle.id,
        reportName=report.name,
        name=request.name.strip(),
        description=request.description,
        defaults=history.defaults,
        inputWindows=history.windows,
        resultPath=result_path,
        revision=1,
    )
    session.add(instance)
    await session.commit()
    return await _response(instance, session)


async def get_instance(
    user_id: int, instance_oid: str, session: AsyncSession
) -> CalcInstanceResDTO:
    """Return one active owned saved instance."""
    instance = await _get_instance_model(user_id, instance_oid, session)
    return await _response(instance, session)


async def count_instances(
    user_id: int,
    filters: CalcInstanceListFilterDTO,
    session: AsyncSession,
) -> int:
    """Count active saved instances matching the supplied filters."""
    conditions = await _instance_list_conditions(user_id, filters, session)
    total = await session.scalar(
        select(func.count(CalcReportInstance.id)).where(*conditions)
    )
    return total or 0


async def list_instances(
    user_id: int,
    filters: CalcInstanceListFilterDTO,
    pagination: PaginationDTO,
    session: AsyncSession,
) -> list[CalcInstanceResDTO]:
    """List one sorted page of active saved instances."""
    conditions = await _instance_list_conditions(user_id, filters, session)
    sort_columns = {
        "id": CalcReportInstance.id,
        "name": CalcReportInstance.name,
        "reportName": CalcReportInstance.reportName,
        "createdAt": CalcReportInstance.createdAt,
        "updatedAt": CalcReportInstance.updatedAt,
    }
    sort_column = sort_columns.get(pagination.sortBy, CalcReportInstance.updatedAt)
    sort_expression = sort_column.desc() if pagination.descending else sort_column.asc()
    stable_sort = (
        CalcReportInstance.id.desc()
        if pagination.descending
        else CalcReportInstance.id.asc()
    )
    instances = (
        await session.scalars(
            select(CalcReportInstance)
            .where(*conditions)
            .order_by(sort_expression, stable_sort)
            .offset(pagination.skip)
            .limit(pagination.limit)
        )
    ).all()
    return [await _response(instance, session) for instance in instances]


async def _instance_list_conditions(
    user_id: int,
    filters: CalcInstanceListFilterDTO,
    session: AsyncSession,
) -> list[Any]:
    """Build shared saved-instance predicates for count and item queries."""
    conditions = [
        CalcReportInstance.userId == user_id,
        CalcReportInstance.deletedAt.is_(None),
    ]
    if filters.categoryOid:
        category = await get_category(user_id, filters.categoryOid, session)
        conditions.append(CalcReportInstance.categoryId == category.id)
    if filters.query:
        pattern = f"%{filters.query.strip()}%"
        conditions.append(
            CalcReportInstance.name.ilike(pattern)
            | CalcReportInstance.description.ilike(pattern)
            | CalcReportInstance.reportName.ilike(pattern)
        )
    return conditions


async def update_instance(
    user_id: int,
    instance_oid: str,
    request: CalcInstanceUpdateDTO,
    session: AsyncSession,
) -> CalcInstanceResDTO:
    """Optimistically update saved-instance metadata."""
    instance = await _get_instance_model(user_id, instance_oid, session)
    category = await get_category(user_id, request.categoryOid, session)
    result = await session.execute(
        update(CalcReportInstance)
        .where(
            CalcReportInstance.id == instance.id,
            CalcReportInstance.revision == request.revision,
            CalcReportInstance.deletedAt.is_(None),
        )
        .values(
            categoryId=category.id,
            name=request.name.strip(),
            description=request.description,
            revision=CalcReportInstance.revision + 1,
        )
    )
    if result.rowcount != 1:
        await session.rollback()
        raise_ex("Instance revision conflict", code=409)
    await session.commit()
    return await get_instance(user_id, instance_oid, session)


async def delete_instance(
    user_id: int, instance_oid: str, session: AsyncSession
) -> None:
    """Physically delete an instance and release its retained report identity.

    Args:
        user_id: Current user database ID.
        instance_oid: Owned instance identifier.
        session: Database session used for deletion and final report cleanup.

    Returns:
        None.

    Raises:
        CustomException: If the instance does not exist or is not owned by the user.
    """
    instance = await _get_instance_model(user_id, instance_oid, session)
    report_id = instance.reportId
    slot = await session.scalar(
        select(CalcExecutionSlot).where(
            CalcExecutionSlot.userId == user_id,
            CalcExecutionSlot.instanceId == instance.id,
        )
    )
    if slot is not None:
        await discard_execution_slot(slot, session)
        await session.delete(slot)
        await session.flush()
    await session.delete(instance)
    await session.commit()
    shutil.rmtree(
        Path("data/calc-instances") / str(user_id) / instance_oid,
        ignore_errors=True,
    )
    report = await session.get(CalcReport, report_id)
    remaining_instances = await session.scalar(
        select(func.count(CalcReportInstance.id)).where(
            CalcReportInstance.reportId == report_id
        )
    )
    if report is not None and report.deletedAt is not None and not remaining_instances:
        from app.service.calc_report_service import delete_report

        await delete_report(user_id, report.oid, session, include_deleted=True)


async def start_instance_execution(
    user_id: int,
    instance_oid: str,
    defaults: dict,
    is_silent: bool,
    session: AsyncSession,
) -> ExecutionStep:
    """Start an execution in the instance-owned retained-result slot."""
    instance = await _get_instance_model(user_id, instance_oid, session)
    report = await session.get(CalcReport, instance.reportId)
    if report is None:
        raise_ex("Calculation report not found", code=404)
    source_type = (
        ExecutionSourceType.VERSION
        if instance.sourceVersionId is not None
        else ExecutionSourceType.WORKSPACE
    )
    version = (
        await session.get(CalcReportVersion, instance.sourceVersionId)
        if instance.sourceVersionId is not None
        else None
    )
    version_name = (
        f"{version.major}.{version.minor}.{version.patch}"
        if version is not None
        else None
    )
    bundle = await session.get(CalcExecutionBundle, instance.bundleId)
    source_artifact = (
        await session.get(CalcReportArtifact, bundle.entrySourceArtifactId)
        if bundle is not None
        else None
    )
    if bundle is None or source_artifact is None:
        raise_ex("Calculation instance bundle is incomplete", code=500)
    slot = await get_or_create_instance_execution_slot(user_id, instance.id, session)
    return await start_execution(
        session,
        user_id,
        CalcExecutionStartDTO(
            reportOid=report.oid,
            source={"type": source_type, "versionName": version_name},
            defaults=defaults,
            isSilent=is_silent,
        ),
        slot_override=slot,
        source_override=ResolvedExecutionSource(
            report=report,
            source_artifact=source_artifact,
            source_type=(
                DbExecutionSourceType.VERSION
                if instance.sourceVersionId is not None
                else DbExecutionSourceType.WORKSPACE
            ),
            resolved_version=version,
        ),
        bundle_override=bundle,
    )


async def get_instance_execution_step(
    user_id: int,
    instance_oid: str,
    session: AsyncSession,
) -> ExecutionStep | None:
    """Return the active or retained execution owned by one instance."""
    instance = await _get_instance_model(user_id, instance_oid, session)
    slot = await session.scalar(
        select(CalcExecutionSlot).where(
            CalcExecutionSlot.userId == user_id,
            CalcExecutionSlot.instanceId == instance.id,
        )
    )
    if slot is None:
        return None
    execution_id = slot.activeExecutionId or slot.currentExecutionId
    execution = await session.get(CalcExecution, execution_id) if execution_id else None
    return (
        await get_execution_step(session, user_id, execution.oid)
        if execution is not None
        else None
    )


async def apply_instance_execution_result(
    user_id: int,
    instance_oid: str,
    execution_oid: str,
    session: AsyncSession,
) -> CalcInstanceResDTO:
    """Promote a successful instance execution into its stable saved result."""
    instance = await _get_instance_model(user_id, instance_oid, session)
    execution, _, _, history = await _execution_source(user_id, execution_oid, session)
    if not execution.resultPath:
        raise_ex("Execution has no cached result", code=409)
    if execution.bundleId != instance.bundleId:
        raise_ex("Execution does not belong to this instance", code=409)
    instance.resultPath = _persist_result(user_id, instance.oid, execution.resultPath)
    instance.defaults = history.defaults
    instance.inputWindows = history.windows
    instance.revision += 1
    await session.commit()
    return await _response(instance, session)


async def share_instance(
    user_id: int, instance_oid: str, session: AsyncSession
) -> CalcInstanceShareResDTO:
    """Create or return the active anonymous share for an owned instance."""
    instance = await _get_instance_model(user_id, instance_oid, session)
    share = await session.scalar(
        select(CalcReportInstanceShare)
        .where(
            CalcReportInstanceShare.instanceId == instance.id,
            CalcReportInstanceShare.revokedAt.is_(None),
            CalcReportInstanceShare.isEnabled.is_(True),
        )
        .order_by(CalcReportInstanceShare.id.desc())
    )
    if share is None:
        share = CalcReportInstanceShare(
            instanceId=instance.id,
            createdByUserId=user_id,
        )
        session.add(share)
        await session.commit()
        await session.refresh(share)
    return _share_response(instance, share)


async def revoke_instance_share(
    user_id: int, instance_oid: str, session: AsyncSession
) -> None:
    """Revoke every active anonymous share for an owned instance."""
    instance = await _get_instance_model(user_id, instance_oid, session)
    now = datetime.datetime.now(datetime.timezone.utc)
    await session.execute(
        update(CalcReportInstanceShare)
        .where(
            CalcReportInstanceShare.instanceId == instance.id,
            CalcReportInstanceShare.revokedAt.is_(None),
        )
        .values(revokedAt=now, isEnabled=False)
    )
    await session.commit()


async def get_public_instance(
    share_token: str, session: AsyncSession
) -> CalcInstanceResDTO:
    """Return one saved instance through a valid anonymous share token."""
    instance = await _get_public_instance_model(share_token, session)
    return await _response(instance, session, public_token=share_token)


async def _get_public_instance_model(
    share_token: str, session: AsyncSession
) -> CalcReportInstance:
    """Load one active saved instance through a valid anonymous share token.

    Args:
        share_token: Signed token identifying the active instance share.
        session: Database session used to resolve the share and instance.

    Returns:
        Active shared calculation instance model.

    Raises:
        CustomException: If the token, share, or instance is unavailable.
    """
    share_oid = verify_signed_share_token("calc-instance", share_token)
    if share_oid is None:
        raise_ex("Shared calculation instance not found", code=404)
    row = (
        await session.execute(
            select(CalcReportInstanceShare, CalcReportInstance)
            .join(
                CalcReportInstance,
                CalcReportInstance.id == CalcReportInstanceShare.instanceId,
            )
            .where(
                CalcReportInstanceShare.oid == share_oid,
                CalcReportInstanceShare.revokedAt.is_(None),
                CalcReportInstanceShare.isEnabled.is_(True),
                CalcReportInstance.deletedAt.is_(None),
            )
        )
    ).one_or_none()
    if row is None:
        raise_ex("Shared calculation instance not found", code=404)
    _, instance = row
    return cast(CalcReportInstance, instance)


async def get_public_instance_result_path(
    share_token: str, session: AsyncSession
) -> Path:
    """Resolve a shared instance's HTML file after token authorization."""
    instance = await _get_public_instance_model(share_token, session)
    relative_path = Path(instance.resultPath)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise_ex("Calculation result path is invalid", code=500)
    result_file = Path("data") / relative_path
    if not result_file.is_file():
        raise_ex("Calculation result file not found", code=404)
    return result_file


async def get_owned_instance_result_path(
    user_id: int, instance_oid: str, session: AsyncSession
) -> Path:
    """Resolve an owned instance's private HTML result file."""
    instance = await _get_instance_model(user_id, instance_oid, session)
    relative_path = Path(instance.resultPath)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise_ex("Calculation result path is invalid", code=500)
    result_file = Path("data") / relative_path
    if not result_file.is_file():
        raise_ex("Calculation result file not found", code=404)
    return result_file


async def _get_instance_model(
    user_id: int, instance_oid: str, session: AsyncSession
) -> CalcReportInstance:
    """Load an active owned instance model."""
    instance = await session.scalar(
        select(CalcReportInstance).where(
            CalcReportInstance.oid == instance_oid,
            CalcReportInstance.userId == user_id,
            CalcReportInstance.deletedAt.is_(None),
        )
    )
    if instance is None:
        raise_ex("Calculation instance not found", code=404)
    return cast(CalcReportInstance, instance)


async def _execution_source(
    user_id: int, execution_oid: str, session: AsyncSession
) -> tuple[CalcExecution, CalcReport, CalcExecutionBundle, UserInputHistory]:
    """Load complete owned execution provenance required by an instance."""
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
    report = await session.get(CalcReport, execution.reportId)
    bundle = await session.get(CalcExecutionBundle, execution.bundleId)
    history = await session.scalar(
        select(UserInputHistory).where(UserInputHistory.executionId == execution.id)
    )
    if report is None or bundle is None or history is None:
        raise_ex("Execution provenance is incomplete", code=500)
    return execution, report, bundle, history


def _persist_result(user_id: int, instance_oid: str, source_result_path: str) -> str:
    """Copy one cached HTML result directory into permanent instance storage."""
    relative = Path(source_result_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise_ex("Execution result path is invalid", code=500)
    source_file = Path("data") / relative
    if not source_file.is_file():
        raise_ex("Calculation result file not found", code=404)
    target_dir = Path("data/calc-instances") / str(user_id) / instance_oid
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_file.parent, target_dir)
    return f"calc-instances/{user_id}/{instance_oid}/{source_file.name}"


async def _response(
    instance: CalcReportInstance,
    session: AsyncSession,
    *,
    public_token: str | None = None,
) -> CalcInstanceResDTO:
    """Build a saved-instance response from normalized provenance relationships."""
    category = await session.get(CalcReportInstanceCategory, instance.categoryId)
    report = await session.get(CalcReport, instance.reportId)
    bundle = await session.get(CalcExecutionBundle, instance.bundleId)
    slot = await session.scalar(
        select(CalcExecutionSlot).where(
            CalcExecutionSlot.userId == instance.userId,
            CalcExecutionSlot.instanceId == instance.id,
        )
    )
    execution = (
        await session.get(CalcExecution, slot.currentExecutionId)
        if slot is not None and slot.currentExecutionId is not None
        else None
    )
    version = (
        await session.get(CalcReportVersion, instance.sourceVersionId)
        if instance.sourceVersionId is not None
        else None
    )
    share = await session.scalar(
        select(CalcReportInstanceShare)
        .where(
            CalcReportInstanceShare.instanceId == instance.id,
            CalcReportInstanceShare.revokedAt.is_(None),
            CalcReportInstanceShare.isEnabled.is_(True),
        )
        .order_by(CalcReportInstanceShare.id.desc())
    )
    share_token = (
        public_token
        if public_token is not None
        else (
            create_signed_share_token("calc-instance", share.oid)
            if share is not None
            else None
        )
    )
    return CalcInstanceResDTO(
        instanceOid=instance.oid,
        categoryOid=category.oid if category is not None else "",
        reportOid=report.oid if report is not None else "",
        reportName=instance.reportName,
        sourceVersion=(
            f"{version.major}.{version.minor}.{version.patch}"
            if version is not None
            else None
        ),
        bundleHash=f"sha256:{bundle.bundleHash}" if bundle is not None else "",
        executionId=execution.oid if execution is not None else None,
        name=instance.name,
        description=instance.description,
        defaults=instance.defaults,
        inputWindows=instance.inputWindows,
        resultPath=(
            f"/api/v1/calc-report-instance/shared/{public_token}/result"
            if public_token is not None
            else f"/v1/calc-report-instance/{instance.oid}/result"
        ),
        isShared=share is not None,
        shareToken=share_token,
        revision=instance.revision,
        createdAt=instance.createdAt,
        updatedAt=instance.updatedAt,
    )


def _share_response(
    instance: CalcReportInstance, share: CalcReportInstanceShare
) -> CalcInstanceShareResDTO:
    """Convert an active instance share into its public token response."""
    return CalcInstanceShareResDTO(
        instanceOid=instance.oid,
        shareOid=share.oid,
        token=create_signed_share_token("calc-instance", share.oid),
        createdAt=share.createdAt,
    )
