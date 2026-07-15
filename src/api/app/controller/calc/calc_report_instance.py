"""HTTP endpoints for bundle-backed saved calculation instances."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_instance_dto import (
    CalcInstanceCreateDTO,
    CalcInstanceListResDTO,
    CalcInstanceResDTO,
    CalcInstanceResultUpdateDTO,
    CalcInstanceUpdateDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_instance_service
from utils.jwt_helper import TokenPayloads

router = APIRouter(prefix="/v1/calc-report-instance", tags=["calc-report-instance"])


@router.get("")
async def list_calc_report_instances(
    categoryOid: str | None = None,
    query: str | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcInstanceListResDTO]:
    """List active saved calculation instances."""
    return ok(
        data=await calc_report_instance_service.list_instances(
            tokenPayloads.id,
            session,
            category_oid=categoryOid,
            query=query,
            offset=offset,
            limit=limit,
        )
    )


@router.post("")
async def create_calc_report_instance(
    request: CalcInstanceCreateDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcInstanceResDTO]:
    """Save a persisted execution as a permanent instance."""
    return ok(
        data=await calc_report_instance_service.create_instance(
            tokenPayloads.id, request, session
        )
    )


@router.get("/{instanceOid}")
async def get_calc_report_instance(
    instanceOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcInstanceResDTO]:
    """Return one active saved instance."""
    return ok(
        data=await calc_report_instance_service.get_instance(
            tokenPayloads.id, instanceOid, session
        )
    )


@router.put("/{instanceOid}")
async def update_calc_report_instance(
    instanceOid: str,
    request: CalcInstanceUpdateDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcInstanceResDTO]:
    """Optimistically update saved-instance metadata."""
    return ok(
        data=await calc_report_instance_service.update_instance(
            tokenPayloads.id, instanceOid, request, session
        )
    )


@router.put("/{instanceOid}/result")
async def update_calc_report_instance_result(
    instanceOid: str,
    request: CalcInstanceResultUpdateDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcInstanceResDTO]:
    """Replace saved result and provenance from another execution."""
    return ok(
        data=await calc_report_instance_service.update_instance_result(
            tokenPayloads.id, instanceOid, request, session
        )
    )


@router.delete("/{instanceOid}")
async def delete_calc_report_instance(
    instanceOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """Soft-delete one saved instance."""
    await calc_report_instance_service.delete_instance(
        tokenPayloads.id, instanceOid, session
    )
    return ok()
