"""HTTP endpoints for bundle-backed saved calculation instances."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_instance_dto import (
    CalcInstanceCreateDTO,
    CalcInstanceListFilterDTO,
    CalcInstanceResDTO,
    CalcInstanceResultUpdateDTO,
    CalcInstanceShareResDTO,
    CalcInstanceUpdateDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.controller.dto_base import PaginationDTO
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_instance_service
from utils.jwt_helper import TokenPayloads

router = APIRouter(prefix="/v1/calc-report-instance", tags=["calc-report-instance"])


@router.get("/shared/{shareToken}")
async def get_public_calc_report_instance(
    shareToken: str,
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcInstanceResDTO]:
    """Return a read-only saved instance through an anonymous share token."""
    return ok(
        data=await calc_report_instance_service.get_public_instance(shareToken, session)
    )


@router.get("/shared/{shareToken}/result")
async def get_public_calc_report_instance_result(
    shareToken: str,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Serve shared instance HTML only after validating its anonymous token."""
    result_path = await calc_report_instance_service.get_public_instance_result_path(
        shareToken, session
    )
    return FileResponse(result_path, media_type="text/html")


@router.get("/count")
async def count_calc_report_instances(
    filters: Annotated[CalcInstanceListFilterDTO, Depends()],
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[int]:
    """Count active saved instances matching the filters."""
    return ok(
        data=await calc_report_instance_service.count_instances(
            tokenPayloads.id, filters, session
        )
    )


@router.get("/items")
async def list_calc_report_instance_items(
    filters: Annotated[CalcInstanceListFilterDTO, Depends()],
    pagination: Annotated[PaginationDTO, Depends()],
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[CalcInstanceResDTO]]:
    """List one sorted page of active saved instances."""
    return ok(
        data=await calc_report_instance_service.list_instances(
            tokenPayloads.id, filters, pagination, session
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


@router.get("/{instanceOid}/result")
async def get_calc_report_instance_result(
    instanceOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Serve an owned saved instance result after authentication."""
    result_path = await calc_report_instance_service.get_owned_instance_result_path(
        tokenPayloads.id, instanceOid, session
    )
    return FileResponse(result_path, media_type="text/html")


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


@router.put("/{instanceOid}/share")
async def share_calc_report_instance(
    instanceOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcInstanceShareResDTO]:
    """Enable anonymous access and return a stable share token."""
    return ok(
        data=await calc_report_instance_service.share_instance(
            tokenPayloads.id, instanceOid, session
        )
    )


@router.delete("/{instanceOid}/share")
async def revoke_calc_report_instance_share(
    instanceOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """Revoke anonymous access to one owned saved instance."""
    await calc_report_instance_service.revoke_instance_share(
        tokenPayloads.id, instanceOid, session
    )
    return ok()
