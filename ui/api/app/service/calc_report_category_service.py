"""
计算分类服务层
负责计算分类的业务逻辑处理
"""

from typing import List, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models.calc_report_category import CalcReportCategory
from app.controller.calc.calc_dto import CategoryInfoReqDTO, CategoryInfoResDTO
from app.exception.custom_exception import raise_ex
from config import logger


async def get_all_categories(
    user_id: int, session: AsyncSession
) -> List[CategoryInfoResDTO]:
    """
    获取当前用户的所有计算分类

    :param user_id: 用户 ID
    :param session: 数据库会话
    :return: 分类信息列表
    """
    result = await session.execute(
        select(CalcReportCategory)
        .where(
            (CalcReportCategory.userId == user_id) & (CalcReportCategory.status == 1)
        )
        .order_by(CalcReportCategory.order)
    )
    categories = result.scalars().all()

    return [
        CategoryInfoResDTO.model_validate(category, from_attributes=True)
        for category in categories
    ]


async def create_category(
    user_id: int, data: CategoryInfoReqDTO, session: AsyncSession
) -> CategoryInfoResDTO:
    """
    创建新的计算分类

    :param user_id: 用户 ID
    :param data: 分类数据
    :param session: 数据库会话
    :return: 创建的分类信息
    """
    # 检查分类名称是否已存在（仅检查状态为 1 的分类）
    existing = await session.scalar(
        select(func.count(CalcReportCategory.id)).where(
            (CalcReportCategory.userId == user_id)
            & (CalcReportCategory.name == data.name)
            & (CalcReportCategory.status == 1)
        )
    )
    if existing and existing > 0:
        raise_ex("Category name already exists", code=400)

    # 获取下一个排序号（最大 order + 1）
    max_order = await session.scalar(
        select(func.max(CalcReportCategory.order)).where(
            CalcReportCategory.userId == user_id
        )
    )
    next_order = (max_order or 0) + 1

    # 创建新分类
    category = CalcReportCategory(
        userId=user_id,
        name=data.name,
        description=data.description,
        cover=data.cover,
        order=next_order,
        total=0,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)

    logger.info(f"分类创建成功: userId={user_id}, categoryId={category.oid}")

    return CategoryInfoResDTO.model_validate(category, from_attributes=True)


async def update_category(
    user_id: int, category_oid: str, data: CategoryInfoReqDTO, session: AsyncSession
) -> CategoryInfoResDTO:
    """
    更新计算分类信息

    :param user_id: 用户 ID
    :param category_id: 分类 ID
    :param data: 更新的分类数据
    :param session: 数据库会话
    :return: 更新后的分类信息
    """
    # 查询分类（确保属于当前用户）
    result = await session.execute(
        select(CalcReportCategory).where(
            (CalcReportCategory.oid == category_oid)
            & (CalcReportCategory.userId == user_id)
        )
    )
    category = result.scalars().first()

    if not category:
        raise_ex("Category not found", code=404)

    category = cast(CalcReportCategory, category)

    # 检查新名称是否与其他分类冲突
    if data.name != category.name:
        existing = await session.scalar(
            select(func.count(CalcReportCategory.id)).where(
                (CalcReportCategory.userId == user_id)
                & (CalcReportCategory.name == data.name)
                & (CalcReportCategory.oid != category_oid)
                & (CalcReportCategory.status == 1)
            )
        )
        if existing and existing > 0:
            raise_ex("Category name already exists", code=400)

    # 更新分类信息
    category.name = data.name
    category.description = data.description

    await session.commit()
    await session.refresh(category)

    logger.info(f"分类更新成功: userId={user_id}, categoryId={category_oid}")

    return CategoryInfoResDTO.model_validate(category, from_attributes=True)


async def update_categories_order(
    user_id: int, category_oids: List[str], session: AsyncSession
) -> None:
    """
    更新分类的排序顺序

    :param user_id: 用户 ID
    :param category_ids: 分类 ID 列表（按新的顺序排列）
    :param session: 数据库会话
    """
    if not category_oids:
        raise_ex("Category IDs list cannot be empty", code=400)

    try:
        # 查询所有分类（确保属于当前用户且状态为 1）
        result = await session.execute(
            select(CalcReportCategory).where(
                (CalcReportCategory.userId == user_id)
                & (CalcReportCategory.oid.in_(category_oids))
                & (CalcReportCategory.status == 1)
            )
        )
        categories = {cat.oid: cat for cat in result.scalars().all()}

        # 验证所有 ID 都存在
        if len(categories) != len(category_oids):
            raise_ex("Some categories not found", code=404)

        # 更新排序
        for order, category_id in enumerate(category_oids):
            categories[category_id].order = order

        await session.commit()

        logger.info(f"分类排序更新成功: userId={user_id}")
    except Exception as e:
        await session.rollback()
        if hasattr(e, "detail"):
            raise e
        logger.error(f"更新分类排序失败: {str(e)}")
        raise_ex("Failed to update categories order", code=500)


async def delete_category(
    user_id: int, category_oid: str, session: AsyncSession
) -> None:
    """
    删除分类（逻辑删除，将 status 设为 0）

    :param user_id: 用户 ID
    :param category_oid: 分类 ID
    :param session: 数据库会话
    """
    # 查询分类
    result = await session.execute(
        select(CalcReportCategory).where(
            (CalcReportCategory.oid == category_oid)
            & (CalcReportCategory.userId == user_id)
            & (CalcReportCategory.status == 1)
        )
    )
    category = result.scalars().first()

    if not category:
        raise_ex("Category not found", code=404)

    category = cast(CalcReportCategory, category)

    # 检查分类是否为空
    if category.total > 0:
        raise_ex("Cannot delete non-empty category", code=400)

    # 逻辑删除：设置 status 为 0
    category.status = 0
    await session.commit()

    logger.info(f"分类删除成功: userId={user_id}, categoryId={category_oid}")
