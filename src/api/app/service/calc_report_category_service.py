"""Database services for calculation-report categories."""

import datetime
from typing import cast

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_report_dto import (
    CalcReportCategoryReqDTO,
    CalcReportCategoryResDTO,
    CategoryOrderDTO,
    CategoryStateDTO,
)
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_category import CalcReportCategory
from app.exception.custom_exception import raise_ex

_LFU_AGING_EPOCH_SECONDS = 7 * 24 * 60 * 60


def _current_aging_epoch(now: datetime.datetime | None = None) -> int:
    """Return the current deterministic seven-day LFU aging epoch.

    Args:
        now: Optional UTC time override used by tests.

    Returns:
        A monotonically increasing integer epoch.

    Raises:
        None.
    """
    current = now or datetime.datetime.now(datetime.timezone.utc)
    return int(current.timestamp()) // _LFU_AGING_EPOCH_SECONDS


async def list_categories(
    user_id: int, session: AsyncSession
) -> list[CalcReportCategoryResDTO]:
    """List active categories with derived active report counts."""
    rows = (
        await session.execute(
            select(
                CalcReportCategory,
                func.count(CalcReport.id),
            )
            .outerjoin(
                CalcReport,
                (CalcReport.categoryId == CalcReportCategory.id)
                & CalcReport.deletedAt.is_(None),
            )
            .where(
                CalcReportCategory.userId == user_id,
                CalcReportCategory.deletedAt.is_(None),
            )
            .group_by(CalcReportCategory.id)
            .order_by(
                case((CalcReportCategory.isPinned.is_(True), 0), else_=1),
                case(
                    (
                        CalcReportCategory.isPinned.is_(True),
                        CalcReportCategory.manualOrder,
                    ),
                    else_=-CalcReportCategory.frequencyCount,
                ),
                CalcReportCategory.lastUsedAt.desc(),
                CalcReportCategory.id,
            )
        )
    ).all()
    return [_category_response(category, count) for category, count in rows]


async def get_category(
    user_id: int, category_oid: str, session: AsyncSession
) -> CalcReportCategory:
    """Load one active owned category or raise a stable not-found error."""
    category = await session.scalar(
        select(CalcReportCategory).where(
            CalcReportCategory.oid == category_oid,
            CalcReportCategory.userId == user_id,
            CalcReportCategory.deletedAt.is_(None),
        )
    )
    if category is None:
        raise_ex(
            "Category not found",
            code=404,
            error_code=CalcErrorCode.CATEGORY_NOT_FOUND,
        )
    return cast(CalcReportCategory, category)


async def create_category(
    user_id: int,
    request: CalcReportCategoryReqDTO,
    session: AsyncSession,
) -> CalcReportCategoryResDTO:
    """Create an active category at the end of the user's ordering."""
    duplicate = await session.scalar(
        select(CalcReportCategory.id).where(
            CalcReportCategory.userId == user_id,
            CalcReportCategory.name == request.name.strip(),
            CalcReportCategory.deletedAt.is_(None),
        )
    )
    if duplicate is not None:
        raise_ex("Category name already exists", code=409)
    maximum = await session.scalar(
        select(func.max(CalcReportCategory.manualOrder)).where(
            CalcReportCategory.userId == user_id,
            CalcReportCategory.deletedAt.is_(None),
        )
    )
    category = CalcReportCategory(
        userId=user_id,
        name=request.name.strip(),
        description=request.description,
        manualOrder=(maximum or 0) + 1,
        agingEpoch=_current_aging_epoch(),
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return _category_response(category, 0)


async def update_category(
    user_id: int,
    category_oid: str,
    request: CalcReportCategoryReqDTO,
    session: AsyncSession,
) -> CalcReportCategoryResDTO:
    """Update category display metadata."""
    category = await get_category(user_id, category_oid, session)
    duplicate = await session.scalar(
        select(CalcReportCategory.id).where(
            CalcReportCategory.userId == user_id,
            CalcReportCategory.name == request.name.strip(),
            CalcReportCategory.id != category.id,
            CalcReportCategory.deletedAt.is_(None),
        )
    )
    if duplicate is not None:
        raise_ex("Category name already exists", code=409)
    category.name = request.name.strip()
    category.description = request.description
    await session.commit()
    await session.refresh(category)
    count = await session.scalar(
        select(func.count(CalcReport.id)).where(
            CalcReport.categoryId == category.id, CalcReport.deletedAt.is_(None)
        )
    )
    return _category_response(category, count or 0)


async def reorder_categories(
    user_id: int, orders: list[CategoryOrderDTO], session: AsyncSession
) -> list[CalcReportCategoryResDTO]:
    """Atomically apply explicit sort orders to all listed owned categories."""
    if len({order.categoryOid for order in orders}) != len(orders):
        raise_ex("Category order contains duplicates", code=400)
    categories = {
        category.oid: category
        for category in (
            await session.scalars(
                select(CalcReportCategory).where(
                    CalcReportCategory.userId == user_id,
                    CalcReportCategory.oid.in_([order.categoryOid for order in orders]),
                    CalcReportCategory.deletedAt.is_(None),
                )
            )
        ).all()
    }
    if len(categories) != len(orders):
        raise_ex(
            "Category not found",
            code=404,
            error_code=CalcErrorCode.CATEGORY_NOT_FOUND,
        )
    for order in orders:
        category = categories[order.categoryOid]
        category.isPinned = True
        category.manualOrder = order.manualOrder
    await session.commit()
    return await list_categories(user_id, session)


async def update_category_state(
    user_id: int,
    category_oid: str,
    request: CategoryStateDTO,
    session: AsyncSession,
) -> CalcReportCategoryResDTO:
    """Update one category's pin and visibility state.

    Args:
        user_id: Authenticated category owner.
        category_oid: Public category identifier.
        request: Optional pin and visibility changes.
        session: Active database session.

    Returns:
        The updated category response.

    Raises:
        CustomException: If the category does not exist.
    """
    category = await get_category(user_id, category_oid, session)
    if request.isPinned is not None:
        category.isPinned = request.isPinned
        if request.isPinned:
            maximum = await session.scalar(
                select(func.max(CalcReportCategory.manualOrder)).where(
                    CalcReportCategory.userId == user_id,
                    CalcReportCategory.isPinned.is_(True),
                    CalcReportCategory.deletedAt.is_(None),
                )
            )
            category.manualOrder = (maximum or 0) + 1
    if request.isHidden is not None:
        category.isHidden = request.isHidden
    await session.commit()
    count = await session.scalar(
        select(func.count(CalcReport.id)).where(
            CalcReport.categoryId == category.id, CalcReport.deletedAt.is_(None)
        )
    )
    return _category_response(category, count or 0)


async def record_category_access(
    user_id: int, category_oid: str, session: AsyncSession
) -> CalcReportCategoryResDTO:
    """Age automatic category counts and record one category activation.

    Args:
        user_id: Authenticated category owner.
        category_oid: Public category identifier being activated.
        session: Active database session.

    Returns:
        The accessed category after LFU-Aging is applied.

    Raises:
        CustomException: If the category does not exist.
    """
    selected_category = await get_category(user_id, category_oid, session)
    current_epoch = _current_aging_epoch()
    categories = (
        await session.scalars(
            select(CalcReportCategory).where(
                CalcReportCategory.userId == user_id,
                CalcReportCategory.isPinned.is_(False),
                CalcReportCategory.isHidden.is_(False),
                CalcReportCategory.deletedAt.is_(None),
            )
        )
    ).all()
    for category in categories:
        elapsed_epochs = max(0, min(31, current_epoch - category.agingEpoch))
        if elapsed_epochs:
            category.frequencyCount >>= elapsed_epochs
            category.agingEpoch = current_epoch
    if not selected_category.isPinned and not selected_category.isHidden:
        selected_category.frequencyCount += 1
        selected_category.agingEpoch = current_epoch
        selected_category.lastUsedAt = datetime.datetime.now(datetime.timezone.utc)
    await session.commit()
    count = await session.scalar(
        select(func.count(CalcReport.id)).where(
            CalcReport.categoryId == selected_category.id,
            CalcReport.deletedAt.is_(None),
        )
    )
    return _category_response(selected_category, count or 0)


async def delete_category(
    user_id: int, category_oid: str, session: AsyncSession
) -> None:
    """Soft-delete an empty category while preserving report ownership."""
    category = await get_category(user_id, category_oid, session)
    report_count = await session.scalar(
        select(func.count(CalcReport.id)).where(
            CalcReport.categoryId == category.id, CalcReport.deletedAt.is_(None)
        )
    )
    if report_count:
        raise_ex("Category contains active reports", code=409)
    category.deletedAt = datetime.datetime.now(datetime.timezone.utc)
    await session.commit()


async def get_or_create_default_category(
    user_id: int, name: str, session: AsyncSession
) -> CalcReportCategoryResDTO:
    """Return an active named category or create it for first-use flows."""
    category = await session.scalar(
        select(CalcReportCategory).where(
            CalcReportCategory.userId == user_id,
            CalcReportCategory.name == name,
            CalcReportCategory.deletedAt.is_(None),
        )
    )
    if category is None:
        return await create_category(
            user_id, CalcReportCategoryReqDTO(name=name), session
        )
    count = await session.scalar(
        select(func.count(CalcReport.id)).where(
            CalcReport.categoryId == category.id, CalcReport.deletedAt.is_(None)
        )
    )
    return _category_response(category, count or 0)


def _category_response(
    category: CalcReportCategory, report_count: int
) -> CalcReportCategoryResDTO:
    """Convert a category model and aggregate count to its public DTO."""
    return CalcReportCategoryResDTO(
        categoryOid=category.oid,
        name=category.name,
        description=category.description,
        manualOrder=category.manualOrder,
        isPinned=category.isPinned,
        isHidden=category.isHidden,
        frequencyCount=category.frequencyCount,
        lastUsedAt=category.lastUsedAt,
        reportCount=report_count,
        createdAt=category.createdAt,
        updatedAt=category.updatedAt,
    )
