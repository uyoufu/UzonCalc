"""HTTP endpoints for CalcReport metadata, copy, and favorites."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_report_dto import (
    CalcReportCopyDTO,
    CalcReportListResDTO,
    CalcReportResDTO,
    CalcReportUpdateDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_service
from utils.jwt_helper import TokenPayloads

router = APIRouter(prefix="/v1/calc-report", tags=["calc-report"])


@router.get("")
async def list_calc_reports(
    categoryOid: str | None = None,
    query: str | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportListResDTO]:
    """List current user's active reports."""
    result = await calc_report_service.list_reports(
        tokenPayloads.id,
        session,
        category_oid=categoryOid,
        query=query,
        offset=offset,
        limit=limit,
    )
    return ok(data=result)


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
