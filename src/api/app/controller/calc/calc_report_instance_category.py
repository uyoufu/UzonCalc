"""HTTP endpoints for saved calculation-instance categories."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_instance_dto import (
    CalcInstanceCategoryReqDTO,
    CalcInstanceCategoryResDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_instance_category_service
from utils.jwt_helper import TokenPayloads

router = APIRouter(
    prefix="/v1/calc-report-instance-category", tags=["calc-report-instance-category"]
)


@router.get("")
async def list_calc_instance_categories(
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[CalcInstanceCategoryResDTO]]:
    """List active instance categories."""
    return ok(
        data=await calc_report_instance_category_service.list_categories(
            tokenPayloads.id, session
        )
    )


@router.post("")
async def create_calc_instance_category(
    request: CalcInstanceCategoryReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcInstanceCategoryResDTO]:
    """Create an instance category."""
    return ok(
        data=await calc_report_instance_category_service.create_category(
            tokenPayloads.id, request, session
        )
    )


@router.post("/default")
async def get_default_calc_instance_category(
    request: CalcInstanceCategoryReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcInstanceCategoryResDTO]:
    """Get or create the named default instance category."""
    return ok(
        data=await calc_report_instance_category_service.get_or_create_default_category(
            tokenPayloads.id, request.name, session
        )
    )


@router.put("/{categoryOid}")
async def update_calc_instance_category(
    categoryOid: str,
    request: CalcInstanceCategoryReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcInstanceCategoryResDTO]:
    """Update instance-category metadata."""
    return ok(
        data=await calc_report_instance_category_service.update_category(
            tokenPayloads.id, categoryOid, request, session
        )
    )


@router.delete("/{categoryOid}")
async def delete_calc_instance_category(
    categoryOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """Soft-delete an empty instance category."""
    await calc_report_instance_category_service.delete_category(
        tokenPayloads.id, categoryOid, session
    )
    return ok()
