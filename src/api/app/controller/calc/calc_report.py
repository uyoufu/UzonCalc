"""HTTP endpoints for CalcReport metadata, copy, and favorites."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_report_dto import (
    CalcReportCopyDTO,
    CalcReportListFilterDTO,
    CalcReportResDTO,
    CalcReportUpdateDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.controller.dto_base import PaginationDTO
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_service
from utils.jwt_helper import TokenPayloads

router = APIRouter(prefix="/v1/calc-report", tags=["calc-report"])


@router.get("/count")
async def count_calc_reports(
    filters: Annotated[CalcReportListFilterDTO, Depends()],
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[int]:
    """Count current user's active reports matching the filters."""
    return ok(
        data=await calc_report_service.count_reports(tokenPayloads.id, filters, session)
    )


@router.get("/items")
async def list_calc_report_items(
    filters: Annotated[CalcReportListFilterDTO, Depends()],
    pagination: Annotated[PaginationDTO, Depends()],
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[CalcReportResDTO]]:
    """List one sorted page of the current user's active reports."""
    return ok(
        data=await calc_report_service.list_reports(
            tokenPayloads.id, filters, pagination, session
        )
    )


@router.get("/{reportOid}")
async def get_calc_report(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportResDTO]:
    """Return one active owned report."""
    return ok(
        data=await calc_report_service.get_report(tokenPayloads.id, reportOid, session)
    )


@router.put("/{reportOid}")
async def update_calc_report(
    reportOid: str,
    request: CalcReportUpdateDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportResDTO]:
    """Update report display metadata."""
    return ok(
        data=await calc_report_service.update_report(
            tokenPayloads.id, reportOid, request, session
        )
    )


@router.post("/{reportOid}/copy")
async def copy_calc_report(
    reportOid: str,
    request: CalcReportCopyDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportResDTO]:
    """Copy an owned report workspace without publishing it."""
    return ok(
        data=await calc_report_service.copy_report(
            tokenPayloads.id, reportOid, request, session
        )
    )


@router.put("/{reportOid}/favorite")
async def favorite_calc_report(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportResDTO]:
    """Mark an owned report as a favorite."""
    return ok(
        data=await calc_report_service.set_favorite(
            tokenPayloads.id, reportOid, True, session
        )
    )


@router.delete("/{reportOid}/favorite")
async def unfavorite_calc_report(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportResDTO]:
    """Remove an owned report from favorites."""
    return ok(
        data=await calc_report_service.set_favorite(
            tokenPayloads.id, reportOid, False, session
        )
    )


@router.delete("/{reportOid}")
async def delete_calc_report(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """Soft-delete an owned report."""
    await calc_report_service.delete_report(tokenPayloads.id, reportOid, session)
    return ok()
