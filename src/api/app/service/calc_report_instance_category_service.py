"""Services for saved calculation-instance categories."""

import datetime
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_instance_dto import (
    CalcInstanceCategoryReqDTO,
    CalcInstanceCategoryResDTO,
)
from app.db.models.calc_report_instance import CalcReportInstance
from app.db.models.calc_report_instance_category import CalcReportInstanceCategory
from app.exception.custom_exception import raise_ex


async def list_categories(
    user_id: int, session: AsyncSession
) -> list[CalcInstanceCategoryResDTO]:
    """List active instance categories with derived counts."""
    rows = (
        await session.execute(
            select(CalcReportInstanceCategory, func.count(CalcReportInstance.id))
            .outerjoin(
                CalcReportInstance,
                (CalcReportInstance.categoryId == CalcReportInstanceCategory.id)
                & CalcReportInstance.deletedAt.is_(None),
            )
            .where(
                CalcReportInstanceCategory.userId == user_id,
                CalcReportInstanceCategory.deletedAt.is_(None),
            )
            .group_by(CalcReportInstanceCategory.id)
            .order_by(
                CalcReportInstanceCategory.sortOrder,
                CalcReportInstanceCategory.id,
            )
        )
    ).all()
    return [_response(category, count) for category, count in rows]


async def get_category(
    user_id: int, category_oid: str, session: AsyncSession
) -> CalcReportInstanceCategory:
    """Load one active owned instance category."""
    category = await session.scalar(
        select(CalcReportInstanceCategory).where(
            CalcReportInstanceCategory.oid == category_oid,
            CalcReportInstanceCategory.userId == user_id,
            CalcReportInstanceCategory.deletedAt.is_(None),
        )
    )
    if category is None:
        raise_ex(
            "Instance category not found",
            code=404,
            error_code=CalcErrorCode.CATEGORY_NOT_FOUND,
        )
    return cast(CalcReportInstanceCategory, category)


async def create_category(
    user_id: int,
    request: CalcInstanceCategoryReqDTO,
    session: AsyncSession,
) -> CalcInstanceCategoryResDTO:
    """Create an instance category at the end of current ordering."""
    maximum = await session.scalar(
        select(func.max(CalcReportInstanceCategory.sortOrder)).where(
            CalcReportInstanceCategory.userId == user_id,
            CalcReportInstanceCategory.deletedAt.is_(None),
        )
    )
    category = CalcReportInstanceCategory(
        userId=user_id,
        name=request.name.strip(),
        description=request.description,
        sortOrder=(maximum or 0) + 1,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return _response(category, 0)


async def update_category(
    user_id: int,
    category_oid: str,
    request: CalcInstanceCategoryReqDTO,
    session: AsyncSession,
) -> CalcInstanceCategoryResDTO:
    """Update instance-category display metadata."""
    category = await get_category(user_id, category_oid, session)
    category.name = request.name.strip()
    category.description = request.description
    await session.commit()
    count = await session.scalar(
        select(func.count(CalcReportInstance.id)).where(
            CalcReportInstance.categoryId == category.id,
            CalcReportInstance.deletedAt.is_(None),
        )
    )
    return _response(category, count or 0)


async def delete_category(
    user_id: int, category_oid: str, session: AsyncSession
) -> None:
    """Soft-delete an empty instance category."""
    category = await get_category(user_id, category_oid, session)
    count = await session.scalar(
        select(func.count(CalcReportInstance.id)).where(
            CalcReportInstance.categoryId == category.id,
            CalcReportInstance.deletedAt.is_(None),
        )
    )
    if count:
        raise_ex("Instance category contains active instances", code=409)
    category.deletedAt = datetime.datetime.now(datetime.timezone.utc)
    await session.commit()


async def get_or_create_default_category(
    user_id: int, name: str, session: AsyncSession
) -> CalcInstanceCategoryResDTO:
    """Return a named active category or create it."""
    category = await session.scalar(
        select(CalcReportInstanceCategory).where(
            CalcReportInstanceCategory.userId == user_id,
            CalcReportInstanceCategory.name == name,
            CalcReportInstanceCategory.deletedAt.is_(None),
        )
    )
    if category is None:
        return await create_category(
            user_id, CalcInstanceCategoryReqDTO(name=name), session
        )
    count = await session.scalar(
        select(func.count(CalcReportInstance.id)).where(
            CalcReportInstance.categoryId == category.id,
            CalcReportInstance.deletedAt.is_(None),
        )
    )
    return _response(category, count or 0)


def _response(
    category: CalcReportInstanceCategory, count: int
) -> CalcInstanceCategoryResDTO:
    """Convert an instance category and derived count to its public DTO."""
    return CalcInstanceCategoryResDTO(
        categoryOid=category.oid,
        name=category.name,
        description=category.description,
        sortOrder=category.sortOrder,
        instanceCount=count,
        createdAt=category.createdAt,
        updatedAt=category.updatedAt,
    )
