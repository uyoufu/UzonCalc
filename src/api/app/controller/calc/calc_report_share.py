"""HTTP endpoints for approved-version sharing and imports."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_share_dto import (
    ShareImportDTO,
    ShareImportResDTO,
    ShareLinkCreateDTO,
    ShareLinkResDTO,
    SharePreviewResDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_share_service
from utils.jwt_helper import TokenPayloads

router = APIRouter(prefix="/v1/calc-report", tags=["calc-report-share"])


@router.post("/{reportOid}/shares")
async def create_calc_report_share(
    reportOid: str,
    request: ShareLinkCreateDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[ShareLinkResDTO]:
    """Create a share link and expose its secret token exactly once."""
    return ok(
        data=await calc_report_share_service.create_share_link(
            tokenPayloads.id, reportOid, request, session
        )
    )


@router.get("/{reportOid}/shares")
async def list_calc_report_shares(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[ShareLinkResDTO]]:
    """List link metadata without returning bearer tokens."""
    return ok(
        data=await calc_report_share_service.list_share_links(
            tokenPayloads.id, reportOid, session
        )
    )


@router.delete("/shares/{shareOid}")
async def revoke_calc_report_share(
    shareOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[ShareLinkResDTO]:
    """Revoke an owned share link idempotently."""
    return ok(
        data=await calc_report_share_service.revoke_share_link(
            tokenPayloads.id, shareOid, session
        )
    )


@router.get("/shared/{token}/preview")
async def preview_shared_calc_report(
    token: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[SharePreviewResDTO]:
    """Preview the authorized approved closure without consuming the link."""
    return ok(
        data=await calc_report_share_service.preview_share(
            tokenPayloads.id, token, session
        )
    )


@router.post("/shared/{token}/import")
async def import_shared_calc_report(
    token: str,
    request: ShareImportDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[ShareImportResDTO]:
    """Import the complete approved closure under receiver ownership."""
    return ok(
        data=await calc_report_share_service.import_share(
            tokenPayloads.id, token, request, session
        )
    )
