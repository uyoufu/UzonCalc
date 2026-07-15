"""HTTP endpoints for immutable report versions and latest pointers."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_report_dto import (
    CalcReportVersionCreateDTO,
    CalcReportVersionResDTO,
    CalcReportVersionReviewDTO,
    VersionNameDTO,
)
from app.controller.calc.calc_workspace_dto import WorkspaceResDTO
from app.controller.depends import get_session, get_token_payload
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_version_service
from utils.jwt_helper import TokenPayloads

router = APIRouter(prefix="/v1/calc-report", tags=["calc-report-version"])


@router.post("/{reportOid}/versions")
async def publish_calc_report_version(
    reportOid: str,
    request: CalcReportVersionCreateDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportVersionResDTO]:
    """Publish current workspace after static validation."""
    return ok(
        data=await calc_report_version_service.publish_version(
            tokenPayloads.id, reportOid, request, session
        )
    )


@router.get("/{reportOid}/versions")
async def list_calc_report_versions(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[CalcReportVersionResDTO]]:
    """List immutable versions for an owned report."""
    return ok(
        data=await calc_report_version_service.list_versions(
            tokenPayloads.id, reportOid, session
        )
    )


@router.put("/{reportOid}/latest")
async def set_calc_report_latest(
    reportOid: str,
    request: VersionNameDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportVersionResDTO]:
    """Move the authoritative latest pointer without changing workspace."""
    return ok(
        data=await calc_report_version_service.set_latest_version(
            tokenPayloads.id, reportOid, request.versionName, session
        )
    )


@router.post("/{reportOid}/workspace/restore")
async def restore_calc_report_workspace(
    reportOid: str,
    request: VersionNameDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[WorkspaceResDTO]:
    """Restore one version into workspace without changing latest."""
    return ok(
        data=await calc_report_version_service.restore_version_workspace(
            tokenPayloads.id, reportOid, request.versionName, session
        )
    )


@router.put("/{reportOid}/versions/{versionName}/review")
async def review_calc_report_version(
    reportOid: str,
    versionName: str,
    request: CalcReportVersionReviewDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[CalcReportVersionResDTO]:
    """Apply an administrator review outcome."""
    return ok(
        data=await calc_report_version_service.review_version(
            tokenPayloads.id,
            tokenPayloads.roles,
            reportOid,
            versionName,
            request,
            session,
        )
    )
