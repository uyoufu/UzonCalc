"""
计算报告服务层
负责计算报告的业务逻辑处理
"""

import os
from typing import List, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_category import CalcReportCategory
from app.controller.calc.calc_dto import (
    CalcReportReqDTO,
    CalcReportResDTO,
    CalcReportListFilterDTO,
    CalcReportCountFilterDTO,
)
from app.exception.custom_exception import raise_ex
from app.utils.path_manager import combine_calc_report_path
from config import logger


async def create_calc_report(
    user_id: int, data: CalcReportReqDTO, session: AsyncSession
) -> CalcReportResDTO:
    """
    创建新的计算报告

    :param user_id: 用户 ID
    :param data: 报告数据
    :param session: 数据库会话
    :return: 创建的报告信息
    """
    # 验证分类存在且属于当前用户
    result = await session.execute(
        select(CalcReportCategory).where(
            (CalcReportCategory.id == data.categoryId)
            & (CalcReportCategory.userId == user_id)
            & (CalcReportCategory.status == 1)
        )
    )
    category = result.scalars().first()

    if not category:
        raise_ex("Category not found", code=404)

    category = cast(CalcReportCategory, category)

    # 创建新报告
    report = CalcReport(
        userId=user_id,
        categoryId=data.categoryId,
        name=data.name,
        description=data.description,
        cover=data.cover,
    )
    session.add(report)

    # 增加分类计数
    category.total += 1

    await session.commit()
    await session.refresh(report)

    logger.info(
        f"计算报告创建成功: userId={user_id}, categoryId={data.categoryId}, reportId={report.oid}"
    )

    return CalcReportResDTO.model_validate(report, from_attributes=True)


async def get_calc_report(report_oid: str, session: AsyncSession) -> CalcReportResDTO:
    """
    获取单个计算报告

    :param user_id: 用户 ID
    :param report_oid: 报告 OID
    :param session: 数据库会话
    :return: 报告信息
    """
    result = await session.execute(
        select(CalcReport).where(
            (CalcReport.oid == report_oid) & (CalcReport.status == 1)
        )
    )
    report = result.scalars().first()

    if not report:
        raise_ex("Report not found", code=404)

    report = cast(CalcReport, report)

    return CalcReportResDTO.model_validate(report, from_attributes=True)


async def list_calc_reports(
    user_id: int, filter_data: CalcReportListFilterDTO, session: AsyncSession
) -> tuple[List[CalcReportResDTO], int]:
    """
    获取计算报告列表（分页）

    :param user_id: 用户 ID
    :param filter_data: 过滤和分页数据
    :param session: 数据库会话
    :return: 报告列表和总数
    """
    # 构建查询条件
    where_clause = (CalcReport.userId == user_id) & (CalcReport.status == 1)

    if filter_data.categoryId:
        where_clause = where_clause & (CalcReport.categoryId == filter_data.categoryId)

    # 获取总数
    count_result = await session.scalar(
        select(func.count(CalcReport.id)).where(where_clause)
    )
    total = count_result or 0

    # 获取分页数据
    result = await session.execute(
        select(CalcReport)
        .where(where_clause)
        .order_by(CalcReport.createdAt.desc())
        .offset(filter_data.pagination.skip)
        .limit(filter_data.pagination.limit)
    )
    reports = result.scalars().all()

    return (
        [
            CalcReportResDTO.model_validate(report, from_attributes=True)
            for report in reports
        ],
        total,
    )


async def count_calc_reports(
    user_id: int, filter_data: CalcReportCountFilterDTO, session: AsyncSession
) -> int:
    """
    统计计算报告数量

    :param user_id: 用户 ID
    :param filter_data: 过滤数据
    :param session: 数据库会话
    :return: 报告数量
    """
    where_clause = (CalcReport.userId == user_id) & (CalcReport.status == 1)

    if filter_data.categoryId:
        where_clause = where_clause & (CalcReport.categoryId == filter_data.categoryId)

    count_result = await session.scalar(
        select(func.count(CalcReport.id)).where(where_clause)
    )
    return count_result or 0


async def update_calc_report(
    user_id: int, report_oid: str, data: CalcReportReqDTO, session: AsyncSession
) -> CalcReportResDTO:
    """
    更新计算报告

    :param user_id: 用户 ID
    :param report_oid: 报告 OID
    :param data: 更新的报告数据
    :param session: 数据库会话
    :return: 更新后的报告信息
    """
    # 获取报告
    result = await session.execute(
        select(CalcReport).where(
            (CalcReport.oid == report_oid)
            & (CalcReport.userId == user_id)
            & (CalcReport.status == 1)
        )
    )
    report = result.scalars().first()

    if not report:
        raise_ex("Report not found", code=404)

    report = cast(CalcReport, report)

    # 如果分类有变化，验证新分类存在且属于当前用户
    if report.categoryId != data.categoryId:
        category_result = await session.execute(
            select(CalcReportCategory).where(
                (CalcReportCategory.id == data.categoryId)
                & (CalcReportCategory.userId == user_id)
                & (CalcReportCategory.status == 1)
            )
        )
        new_category = category_result.scalars().first()

        if not new_category:
            raise_ex("Category not found", code=404)

        new_category = cast(CalcReportCategory, new_category)

        # 更新旧分类计数
        old_category_result = await session.execute(
            select(CalcReportCategory).where(CalcReportCategory.id == report.categoryId)
        )
        old_category = old_category_result.scalars().first()
        if old_category:
            old_category.total = max(0, old_category.total - 1)

        # 更新新分类计数
        new_category.total += 1

    # 更新报告信息
    report.name = data.name
    report.description = data.description
    if data.cover is not None:
        report.cover = data.cover
    report.categoryId = data.categoryId

    await session.commit()
    await session.refresh(report)

    logger.info(f"计算报告更新成功: userId={user_id}, reportOid={report_oid}")

    return CalcReportResDTO.model_validate(report, from_attributes=True)


async def delete_calc_report(
    user_id: int, report_oid: str, session: AsyncSession
) -> None:
    """
    删除计算报告（逻辑删除，将 status 设为 0）

    :param user_id: 用户 ID
    :param report_oid: 报告 OID
    :param session: 数据库会话
    """
    # 获取报告
    result = await session.execute(
        select(CalcReport).where(
            (CalcReport.oid == report_oid)
            & (CalcReport.userId == user_id)
            & (CalcReport.status == 1)
        )
    )
    report = result.scalars().first()

    if not report:
        raise_ex("Report not found", code=404)

    report = cast(CalcReport, report)

    # 逻辑删除：设置 status 为 0
    report.status = 0

    # 减少分类计数
    category_result = await session.execute(
        select(CalcReportCategory).where(CalcReportCategory.id == report.categoryId)
    )
    category = category_result.scalars().first()
    if category:
        category.total = max(0, category.total - 1)

    await session.commit()

    logger.info(f"计算报告删除成功: userId={user_id}, reportOid={report_oid}")


async def batch_delete_calc_reports(
    user_id: int, report_oids: List[str], session: AsyncSession
) -> int:
    """
    批量删除计算报告（逻辑删除）

    :param user_id: 用户 ID
    :param report_oids: 报告 OID 列表
    :param session: 数据库会话
    :return: 删除的报告数量
    """
    if not report_oids:
        return 0

    # 获取所有要删除的报告
    result = await session.execute(
        select(CalcReport).where(
            (CalcReport.userId == user_id)
            & (CalcReport.oid.in_(report_oids))
            & (CalcReport.status == 1)
        )
    )
    reports = result.scalars().all()

    if not reports:
        return 0

    # 按分类统计删除的报告数量
    category_count_map: dict[int, int] = {}
    for report in reports:
        if report.categoryId not in category_count_map:
            category_count_map[report.categoryId] = 0
        category_count_map[report.categoryId] += 1

    # 更新所有报告状态
    for report in reports:
        report.status = 0

    # 更新分类计数
    if category_count_map:
        category_result = await session.execute(
            select(CalcReportCategory).where(
                CalcReportCategory.id.in_(category_count_map.keys())
            )
        )
        categories = category_result.scalars().all()
        for category in categories:
            delete_count = category_count_map.get(category.id, 0)
            category.total = max(0, category.total - delete_count)

    await session.commit()

    logger.info(f"计算报告批量删除成功: userId={user_id}, count={len(reports)}")

    return len(reports)


async def save_or_update_calc_report(
    user_id: int,
    report_name: str | None,
    report_oid: str | None,
    category_oid: str | None,
    session: AsyncSession,
) -> CalcReportResDTO:
    """
    保存或更新计算报告

    若 report_oid 为 None，则创建新报告；否则更新现有报告

    :param user_id: 用户 ID
    :param report_name: 报告名称
    :param report_oid: 报告 OID（可选）
    :param category_oid: 分类 OID（新增时需要）
    :param session: 数据库会话
    :return: 报告信息（包含 oid）
    """
    if not report_name:
        raise_ex("reportName is required", code=400)

    # 先按 userId + name 判断唯一性
    report = await session.scalar(
        select(CalcReport).where(
            (CalcReport.userId == user_id)
            & (CalcReport.name == report_name)
            & (CalcReport.status == 1)
        )
    )

    # 若未找到，再根据 report_oid 回退查找（用于重命名场景）
    if not report and report_oid:
        report = await session.scalar(
            select(CalcReport).where(CalcReport.oid == report_oid)
        )

    if report:
        report = cast(CalcReport, report)
        old_name = report.name
        old_category_id = report.categoryId

        # 若提供新的分类 oid，则校验并更新
        new_category: CalcReportCategory | None = None
        if category_oid:
            new_category = await session.scalar(
                select(CalcReportCategory).where(
                    (CalcReportCategory.oid == category_oid)
                    & (CalcReportCategory.userId == user_id)
                    & (CalcReportCategory.status == 1)
                )
            )
            if not new_category:
                raise_ex("Category not found", code=404)
            new_category = cast(CalcReportCategory, new_category)
            report.categoryId = new_category.id

        # 处理改名时的旧文件清理
        if old_name != report_name:
            old_file_path = combine_calc_report_path(user_id, old_name)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)

        report.name = cast(str, report_name)

        # 分类计数同步：若分类变更，旧分类 -1，新分类 +1
        if new_category and new_category.id != old_category_id:
            old_category = await session.scalar(
                select(CalcReportCategory).where(
                    (CalcReportCategory.id == old_category_id)
                    & (CalcReportCategory.userId == user_id)
                )
            )
            if old_category:
                old_category.total = max(0, old_category.total - 1)

            new_category.total += 1

        await session.commit()
        await session.refresh(report)

        logger.info(
            f"计算报告文件更新: userId={user_id}, "
            f"reportOid={report.oid}, reportName={report_name}"
        )
    else:
        # 创建新报告，需要 category_oid
        if not category_oid:
            raise_ex("categoryOid is required for creating new report", code=400)

        # 根据 oid 查找分类
        category = await session.scalar(
            select(CalcReportCategory).where(
                (CalcReportCategory.oid == category_oid)
                & (CalcReportCategory.userId == user_id)
                & (CalcReportCategory.status == 1)
            )
        )

        if not category:
            raise_ex("Category not found", code=404)

        category = cast(CalcReportCategory, category)

        # 创建新报告
        report = CalcReport(
            userId=user_id,
            categoryId=category.id,
            name=report_name,
        )
        session.add(report)

        # 增加分类计数
        category.total += 1

        await session.commit()
        await session.refresh(report)

        logger.info(
            f"计算报告文件新增: userId={user_id}, "
            f"reportOid={report.oid}, reportName={report_name}, categoryOid={category_oid}"
        )

    return CalcReportResDTO.model_validate(report, from_attributes=True)
