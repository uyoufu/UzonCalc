"""
计算实例服务层
负责计算实例的列表、保存和结果文件固化。
"""

import datetime
import shutil
from pathlib import Path
from typing import List, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_dto import (
    CalcReportInstanceCountFilterDTO,
    CalcReportInstanceListFilterDTO,
    CalcReportInstanceReqDTO,
    CalcReportInstanceResDTO,
    CalcReportInstanceSaveReqDTO,
)
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_instance import CalcReportInstance
from app.db.models.calc_report_instance_category import CalcReportInstanceCategory
from app.exception.custom_exception import raise_ex
from config import logger


def _build_instance_result_path(
    user_id: int, instance_oid: str, source_result_path: str
) -> str:
    source_file = Path("data") / source_result_path
    if not source_file.exists() or not source_file.is_file():
        raise_ex("Calculation result file not found", code=404)

    target_dir = (
        Path("data") / "public" / "calc-instances" / str(user_id) / instance_oid
    )
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_file.parent, target_dir)

    target_file = target_dir / source_file.name
    return f"public/calc-instances/{user_id}/{instance_oid}/{target_file.name}"


def _to_instance_res(
    instance: CalcReportInstance, report_oid: str
) -> CalcReportInstanceResDTO:
    return CalcReportInstanceResDTO(
        id=instance.id,
        oid=instance.oid,
        userId=instance.userId,
        categoryId=instance.categoryId,
        reportId=instance.reportId,
        reportOid=report_oid,
        reportName=instance.reportName,
        name=instance.name,
        description=instance.description,
        defaults=instance.defaults or {},
        resultPath=instance.resultPath,
        createdAt=instance.createdAt,
        version=instance.version,
        lastModified=instance.lastModified,
    )


async def _get_source_report(
    user_id: int, report_oid: str, session: AsyncSession
) -> CalcReport:
    report = await session.scalar(
        select(CalcReport).where(
            (CalcReport.oid == report_oid)
            & (CalcReport.userId == user_id)
            & (CalcReport.status == 1)
        )
    )
    if not report:
        raise_ex("Report not found", code=404)
    return cast(CalcReport, report)


async def _get_category(
    user_id: int, category_id: int, session: AsyncSession
) -> CalcReportInstanceCategory:
    category = await session.scalar(
        select(CalcReportInstanceCategory).where(
            (CalcReportInstanceCategory.id == category_id)
            & (CalcReportInstanceCategory.userId == user_id)
            & (CalcReportInstanceCategory.status == 1)
        )
    )
    if not category:
        raise_ex("Category not found", code=404)
    return cast(CalcReportInstanceCategory, category)


async def save_calc_report_instance(
    user_id: int, data: CalcReportInstanceSaveReqDTO, session: AsyncSession
) -> CalcReportInstanceResDTO:
    """新增计算实例，并将临时 HTML 结果复制到永久实例目录。"""
    report = await _get_source_report(user_id, data.reportOid, session)
    category = await _get_category(user_id, data.categoryId, session)

    instance = CalcReportInstance(
        userId=user_id,
        categoryId=category.id,
        reportId=report.id,
        reportName=report.name,
        name=data.name,
        description=data.description,
        defaults=data.defaults,
        resultPath=None,
    )
    session.add(instance)
    category.total += 1

    try:
        await session.flush()
        instance.resultPath = _build_instance_result_path(
            user_id, instance.oid, data.resultPath
        )
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception(
            "保存计算实例失败: userId=%s, reportOid=%s", user_id, data.reportOid
        )
        raise

    await session.refresh(instance)
    return _to_instance_res(instance, report.oid)


async def get_calc_report_instance(
    user_id: int, instance_oid: str, session: AsyncSession
) -> CalcReportInstanceResDTO:
    instance = await session.scalar(
        select(CalcReportInstance).where(
            (CalcReportInstance.oid == instance_oid)
            & (CalcReportInstance.userId == user_id)
            & (CalcReportInstance.status == 1)
        )
    )
    if not instance:
        raise_ex("Calculation instance not found", code=404)
    instance = cast(CalcReportInstance, instance)

    report = await session.scalar(
        select(CalcReport).where(CalcReport.id == instance.reportId)
    )
    report_oid = report.oid if report else ""
    return _to_instance_res(instance, report_oid)


async def list_calc_report_instances(
    user_id: int, filter_data: CalcReportInstanceListFilterDTO, session: AsyncSession
) -> tuple[List[CalcReportInstanceResDTO], int]:
    where_clause = (CalcReportInstance.userId == user_id) & (
        CalcReportInstance.status == 1
    )
    if filter_data.categoryId:
        where_clause = where_clause & (
            CalcReportInstance.categoryId == filter_data.categoryId
        )
    if filter_data.filter:
        like_pattern = f"%{filter_data.filter}%"
        where_clause = where_clause & (
            (CalcReportInstance.name.ilike(like_pattern))
            | (CalcReportInstance.description.ilike(like_pattern))
            | (CalcReportInstance.reportName.ilike(like_pattern))
        )

    total = await session.scalar(
        select(func.count(CalcReportInstance.id)).where(where_clause)
    )
    result = await session.execute(
        select(CalcReportInstance, CalcReport.oid)
        .outerjoin(CalcReport, CalcReport.id == CalcReportInstance.reportId)
        .where(where_clause)
        .order_by(CalcReportInstance.createdAt.desc())
        .offset(filter_data.pagination.skip)
        .limit(filter_data.pagination.limit)
    )

    items = [
        _to_instance_res(instance, report_oid or "")
        for instance, report_oid in result.all()
    ]
    return items, total or 0


async def count_calc_report_instances(
    user_id: int, filter_data: CalcReportInstanceCountFilterDTO, session: AsyncSession
) -> int:
    where_clause = (CalcReportInstance.userId == user_id) & (
        CalcReportInstance.status == 1
    )
    if filter_data.categoryId:
        where_clause = where_clause & (
            CalcReportInstance.categoryId == filter_data.categoryId
        )
    if filter_data.filter:
        like_pattern = f"%{filter_data.filter}%"
        where_clause = where_clause & (
            (CalcReportInstance.name.ilike(like_pattern))
            | (CalcReportInstance.description.ilike(like_pattern))
            | (CalcReportInstance.reportName.ilike(like_pattern))
        )

    total = await session.scalar(
        select(func.count(CalcReportInstance.id)).where(where_clause)
    )
    return total or 0


async def update_calc_report_instance_info(
    user_id: int,
    instance_oid: str,
    data: CalcReportInstanceReqDTO,
    session: AsyncSession,
) -> CalcReportInstanceResDTO:
    instance = await session.scalar(
        select(CalcReportInstance).where(
            (CalcReportInstance.oid == instance_oid)
            & (CalcReportInstance.userId == user_id)
            & (CalcReportInstance.status == 1)
        )
    )
    if not instance:
        raise_ex("Calculation instance not found", code=404)
    instance = cast(CalcReportInstance, instance)

    old_category = await _get_category(user_id, instance.categoryId, session)
    new_category = old_category
    if instance.categoryId != data.categoryId:
        new_category = await _get_category(user_id, data.categoryId, session)
        old_category.total = max(0, old_category.total - 1)
        new_category.total += 1

    instance.categoryId = new_category.id
    instance.name = data.name
    instance.description = data.description
    instance.version += 1
    instance.lastModified = datetime.datetime.now(datetime.timezone.utc)

    await session.commit()
    await session.refresh(instance)
    report = await session.scalar(
        select(CalcReport).where(CalcReport.id == instance.reportId)
    )
    return _to_instance_res(instance, report.oid if report else "")


async def update_calc_report_instance_result(
    user_id: int,
    instance_oid: str,
    data: CalcReportInstanceSaveReqDTO,
    session: AsyncSession,
) -> CalcReportInstanceResDTO:
    instance = await session.scalar(
        select(CalcReportInstance).where(
            (CalcReportInstance.oid == instance_oid)
            & (CalcReportInstance.userId == user_id)
            & (CalcReportInstance.status == 1)
        )
    )
    if not instance:
        raise_ex("Calculation instance not found", code=404)
    instance = cast(CalcReportInstance, instance)

    report = await _get_source_report(user_id, data.reportOid, session)
    category = await _get_category(user_id, data.categoryId, session)

    instance.categoryId = category.id
    instance.reportId = report.id
    instance.reportName = report.name
    instance.name = data.name
    instance.description = data.description
    instance.defaults = data.defaults
    instance.resultPath = _build_instance_result_path(
        user_id, instance.oid, data.resultPath
    )
    instance.version += 1
    instance.lastModified = datetime.datetime.now(datetime.timezone.utc)

    await session.commit()
    await session.refresh(instance)
    return _to_instance_res(instance, report.oid)


async def delete_calc_report_instance(
    user_id: int, instance_oid: str, session: AsyncSession
) -> None:
    instance = await session.scalar(
        select(CalcReportInstance).where(
            (CalcReportInstance.oid == instance_oid)
            & (CalcReportInstance.userId == user_id)
            & (CalcReportInstance.status == 1)
        )
    )
    if not instance:
        raise_ex("Calculation instance not found", code=404)
    instance = cast(CalcReportInstance, instance)
    instance.status = 0

    category = await session.scalar(
        select(CalcReportInstanceCategory).where(
            CalcReportInstanceCategory.id == instance.categoryId
        )
    )
    if category:
        category.total = max(0, category.total - 1)

    await session.commit()
