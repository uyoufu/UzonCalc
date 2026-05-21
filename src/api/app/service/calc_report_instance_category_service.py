"""
计算实例分类服务层
"""

from typing import List, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_dto import CategoryInfoReqDTO, CategoryInfoResDTO
from app.db.models.calc_report_instance_category import CalcReportInstanceCategory
from app.exception.custom_exception import raise_ex
from config import logger


async def get_all_categories(
    user_id: int, session: AsyncSession
) -> List[CategoryInfoResDTO]:
    result = await session.execute(
        select(CalcReportInstanceCategory)
        .where(
            (CalcReportInstanceCategory.userId == user_id)
            & (CalcReportInstanceCategory.status == 1)
        )
        .order_by(CalcReportInstanceCategory.order)
    )
    return [
        CategoryInfoResDTO.model_validate(category, from_attributes=True)
        for category in result.scalars().all()
    ]


async def get_category_by_oid(
    user_id: int, category_oid: str, session: AsyncSession
) -> CategoryInfoResDTO:
    category = await session.scalar(
        select(CalcReportInstanceCategory).where(
            (CalcReportInstanceCategory.oid == category_oid)
            & (CalcReportInstanceCategory.userId == user_id)
            & (CalcReportInstanceCategory.status == 1)
        )
    )
    if not category:
        raise_ex("Category not found", code=404)
    return CategoryInfoResDTO.model_validate(category, from_attributes=True)


async def create_category(
    user_id: int, data: CategoryInfoReqDTO, session: AsyncSession
) -> CategoryInfoResDTO:
    existing = await session.scalar(
        select(func.count(CalcReportInstanceCategory.id)).where(
            (CalcReportInstanceCategory.userId == user_id)
            & (CalcReportInstanceCategory.name == data.name)
            & (CalcReportInstanceCategory.status == 1)
        )
    )
    if existing and existing > 0:
        raise_ex("Category name already exists", code=400)

    max_order = await session.scalar(
        select(func.max(CalcReportInstanceCategory.order)).where(
            CalcReportInstanceCategory.userId == user_id
        )
    )
    category = CalcReportInstanceCategory(
        userId=user_id,
        name=data.name,
        description=data.description,
        order=(max_order or 0) + 1,
        total=0,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    logger.info("计算实例分类创建成功: userId=%s, categoryOid=%s", user_id, category.oid)
    return CategoryInfoResDTO.model_validate(category, from_attributes=True)


async def update_category(
    user_id: int, category_oid: str, data: CategoryInfoReqDTO, session: AsyncSession
) -> CategoryInfoResDTO:
    category = await session.scalar(
        select(CalcReportInstanceCategory).where(
            (CalcReportInstanceCategory.oid == category_oid)
            & (CalcReportInstanceCategory.userId == user_id)
            & (CalcReportInstanceCategory.status == 1)
        )
    )
    if not category:
        raise_ex("Category not found", code=404)
    category = cast(CalcReportInstanceCategory, category)

    if data.name != category.name:
        existing = await session.scalar(
            select(func.count(CalcReportInstanceCategory.id)).where(
                (CalcReportInstanceCategory.userId == user_id)
                & (CalcReportInstanceCategory.name == data.name)
                & (CalcReportInstanceCategory.oid != category_oid)
                & (CalcReportInstanceCategory.status == 1)
            )
        )
        if existing and existing > 0:
            raise_ex("Category name already exists", code=400)

    category.name = data.name
    category.description = data.description
    await session.commit()
    await session.refresh(category)
    return CategoryInfoResDTO.model_validate(category, from_attributes=True)


async def delete_category(
    user_id: int, category_oid: str, session: AsyncSession
) -> None:
    category = await session.scalar(
        select(CalcReportInstanceCategory).where(
            (CalcReportInstanceCategory.oid == category_oid)
            & (CalcReportInstanceCategory.userId == user_id)
            & (CalcReportInstanceCategory.status == 1)
        )
    )
    if not category:
        raise_ex("Category not found", code=404)
    category = cast(CalcReportInstanceCategory, category)

    if category.total > 0:
        raise_ex("Cannot delete non-empty category", code=400)

    category.status = 0
    await session.commit()


async def get_or_create_default_category(
    user_id: int, default_category_name: str, session: AsyncSession
) -> CategoryInfoResDTO:
    category = await session.scalar(
        select(CalcReportInstanceCategory)
        .where(
            (CalcReportInstanceCategory.userId == user_id)
            & (CalcReportInstanceCategory.status == 1)
        )
        .order_by(CalcReportInstanceCategory.order)
        .limit(1)
    )
    if category:
        return CategoryInfoResDTO.model_validate(category, from_attributes=True)

    return await create_category(
        user_id,
        CategoryInfoReqDTO(name=default_category_name, description=None),
        session,
    )
