"""Bundle-backed saved calculation-instance services."""

import datetime
import shutil
from pathlib import Path
from typing import cast

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_instance_dto import (
    CalcInstanceCreateDTO,
    CalcInstanceListResDTO,
    CalcInstanceResDTO,
    CalcInstanceResultUpdateDTO,
    CalcInstanceUpdateDTO,
)
from app.db.models.calc_execution import CalcExecution, CalcExecutionBundle
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_instance import CalcReportInstance
from app.db.models.calc_report_instance_category import CalcReportInstanceCategory
from app.db.models.calc_report_version import CalcReportVersion
from app.db.models.user_input_history import UserInputHistory
from app.exception.custom_exception import raise_ex
from app.service.calc_report_instance_category_service import get_category


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
    instance = CalcReportInstance(
        userId=user_id,
        categoryId=category.id,
        reportId=report.id,
        sourceVersionId=execution.resolvedVersionId,
        bundleId=bundle.id,
        executionId=execution.id,
        reportName=report.name,
        name=request.name.strip(),
        description=request.description,
        defaults=history.defaults,
        resultPath="pending",
        revision=1,
    )
    session.add(instance)
    await session.flush()
    instance.resultPath = _persist_result(user_id, instance.oid, execution.resultPath)
    await session.commit()
    return await _response(instance, session)


async def get_instance(
    user_id: int, instance_oid: str, session: AsyncSession
) -> CalcInstanceResDTO:
    """Return one active owned saved instance."""
    instance = await _get_instance_model(user_id, instance_oid, session)
    return await _response(instance, session)


async def list_instances(
    user_id: int,
    session: AsyncSession,
    *,
    category_oid: str | None = None,
    query: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> CalcInstanceListResDTO:
    """List active saved instances with total count."""
    conditions = [
        CalcReportInstance.userId == user_id,
        CalcReportInstance.deletedAt.is_(None),
    ]
    if category_oid:
        category = await get_category(user_id, category_oid, session)
        conditions.append(CalcReportInstance.categoryId == category.id)
    if query:
        pattern = f"%{query.strip()}%"
        conditions.append(
            CalcReportInstance.name.ilike(pattern)
            | CalcReportInstance.description.ilike(pattern)
            | CalcReportInstance.reportName.ilike(pattern)
        )
    total = await session.scalar(
        select(func.count(CalcReportInstance.id)).where(*conditions)
    )
    instances = (
        await session.scalars(
            select(CalcReportInstance)
            .where(*conditions)
            .order_by(CalcReportInstance.updatedAt.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return CalcInstanceListResDTO(
        items=[await _response(instance, session) for instance in instances],
        total=total or 0,
    )


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


async def update_instance_result(
    user_id: int,
    instance_oid: str,
    request: CalcInstanceResultUpdateDTO,
    session: AsyncSession,
) -> CalcInstanceResDTO:
    """Replace result/provenance from a newer owned execution."""
    instance = await _get_instance_model(user_id, instance_oid, session)
    execution, report, bundle, history = await _execution_source(
        user_id, request.executionId, session
    )
    if request.revision != instance.revision:
        raise_ex("Instance revision conflict", code=409)
    if not execution.resultPath:
        raise_ex("Execution has no cached result", code=409)
    result_path = _persist_result(user_id, instance.oid, execution.resultPath)
    instance.reportId = report.id
    instance.sourceVersionId = execution.resolvedVersionId
    instance.bundleId = bundle.id
    instance.executionId = execution.id
    instance.reportName = report.name
    instance.defaults = history.defaults
    instance.resultPath = result_path
    instance.revision += 1
    await session.commit()
    return await _response(instance, session)


async def delete_instance(
    user_id: int, instance_oid: str, session: AsyncSession
) -> None:
    """Soft-delete an owned saved instance while retaining reproducibility rows."""
    instance = await _get_instance_model(user_id, instance_oid, session)
    instance.deletedAt = datetime.datetime.now(datetime.timezone.utc)
    await session.commit()


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
    target_dir = Path("data/public/calc-instances") / str(user_id) / instance_oid
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_file.parent, target_dir)
    return f"public/calc-instances/{user_id}/{instance_oid}/{source_file.name}"


async def _response(
    instance: CalcReportInstance, session: AsyncSession
) -> CalcInstanceResDTO:
    """Build a saved-instance response from normalized provenance relationships."""
    category = await session.get(CalcReportInstanceCategory, instance.categoryId)
    report = await session.get(CalcReport, instance.reportId)
    bundle = await session.get(CalcExecutionBundle, instance.bundleId)
    execution = (
        await session.get(CalcExecution, instance.executionId)
        if instance.executionId is not None
        else None
    )
    version = (
        await session.get(CalcReportVersion, instance.sourceVersionId)
        if instance.sourceVersionId is not None
        else None
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
        resultPath=instance.resultPath,
        revision=instance.revision,
        createdAt=instance.createdAt,
        updatedAt=instance.updatedAt,
    )
