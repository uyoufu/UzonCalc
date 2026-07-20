"""HTTP endpoints for calculation-report categories."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_report_dto import (
    CalcReportCategoryReqDTO,
    CalcReportCategoryResDTO,
    CategoryOrderDTO,
    CategoryStateDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_category_service
from utils.jwt_helper import TokenPayloads

router = APIRouter(prefix="/v1/calc-report-category", tags=["calc-report-category"])


@router.get("")
async def list_calc_report_categories(
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[CalcReportCategoryResDTO]]:
    """List current user's active report categories."""
    return ok(
        data=await calc_report_category_service.list_categories(
            tokenPayloads.id, session
        )
    )


@router.post("")
async def create_calc_report_category(
    request: CalcReportCategoryReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportCategoryResDTO]:
    """Create a report category."""
    return ok(
        data=await calc_report_category_service.create_category(
            tokenPayloads.id, request, session
        )
    )


@router.post("/default")
async def get_default_calc_report_category(
    request: CalcReportCategoryReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportCategoryResDTO]:
    """Get or create the named default category."""
    return ok(
        data=await calc_report_category_service.get_or_create_default_category(
            tokenPayloads.id, request.name, session
        )
    )


@router.put("/order")
async def reorder_calc_report_categories(
    orders: list[CategoryOrderDTO],
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[CalcReportCategoryResDTO]]:
    """Replace explicit category sort orders."""
    return ok(
        data=await calc_report_category_service.reorder_categories(
            tokenPayloads.id, orders, session
        )
    )


@router.put("/{categoryOid}/state")
async def update_calc_report_category_state(
    categoryOid: str,
    request: CategoryStateDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportCategoryResDTO]:
    """Update category pinning and visibility state."""
    return ok(
        data=await calc_report_category_service.update_category_state(
            tokenPayloads.id, categoryOid, request, session
        )
    )


@router.post("/{categoryOid}/access")
async def record_calc_report_category_access(
    categoryOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportCategoryResDTO]:
    """Record one category activation for LFU-Aging ordering."""
    return ok(
        data=await calc_report_category_service.record_category_access(
            tokenPayloads.id, categoryOid, session
        )
    )


@router.put("/{categoryOid}")
async def update_calc_report_category(
    categoryOid: str,
    request: CalcReportCategoryReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportCategoryResDTO]:
    """Update category metadata."""
    return ok(
        data=await calc_report_category_service.update_category(
            tokenPayloads.id, categoryOid, request, session
        )
    )


@router.delete("/{categoryOid}")
async def delete_calc_report_category(
    categoryOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """Soft-delete an empty category."""
    await calc_report_category_service.delete_category(
        tokenPayloads.id, categoryOid, session
    )
    return ok()
