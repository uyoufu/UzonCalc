"""HTTP endpoints for version sharing, discovery, imports, and synchronization."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_share_dto import (
    ShareImportDTO,
    ShareImportResDTO,
    ReportSyncResDTO,
    ShareCatalogFilterDTO,
    ShareLinkCreateDTO,
    ShareLinkResDTO,
    SharePreviewResDTO,
    SharedReportResDTO,
    ShareDepartmentOptionDTO,
    ShareUserOptionDTO,
)
from app.controller.depends import (
    get_optional_token_payload,
    get_session,
    get_token_payload,
)
from app.controller.dto_base import PaginationDTO
from app.middleware.authentication import allow_anonymous
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_archive_service, calc_report_share_service
from app.db.models.calc_report_share import CalcReportShareLink
from app.controller.calc.calc_execution import (
    execution_step_response,
    finalize_execution_step,
)
from utils.jwt_helper import TokenPayloads

router = APIRouter(prefix="/v1/calc-report", tags=["calc-report-share"])


@router.get("/share-directory/users")
async def list_share_user_options(
    query: str | None = None,
    _tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[ShareUserOptionDTO]]:
    """Search active users that may receive a specified-users share."""
    return ok(
        data=await calc_report_share_service.list_share_user_options(query, session)
    )


@router.get("/share-directory/departments")
async def list_share_department_options(
    _tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[ShareDepartmentOptionDTO]]:
    """List active departments that may receive a department share."""
    return ok(
        data=await calc_report_share_service.list_share_department_options(session)
    )


@router.get("/shared/count")
async def count_shared_calc_reports(
    filters: Annotated[ShareCatalogFilterDTO, Depends()],
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[int]:
    """Count share catalog entries available to the current user."""
    return ok(
        data=await calc_report_share_service.count_available_shares(
            tokenPayloads.id, filters, session
        )
    )


@router.get("/shared/items")
async def list_shared_calc_reports(
    filters: Annotated[ShareCatalogFilterDTO, Depends()],
    pagination: Annotated[PaginationDTO, Depends()],
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[SharedReportResDTO]]:
    """List one page of share catalog entries available to the current user."""
    return ok(
        data=await calc_report_share_service.list_available_shares(
            tokenPayloads.id, filters, pagination, session
        )
    )


@router.post("/{reportOid}/shares")
async def create_calc_report_share(
    reportOid: str,
    request: ShareLinkCreateDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[ShareLinkResDTO]:
    """Create a share link and return its stable owner-visible token."""
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
    """List owned link metadata with stable owner-visible tokens."""
    return ok(
        data=await calc_report_share_service.list_share_links(
            tokenPayloads.id, reportOid, session
        )
    )


@router.put("/shares/{shareOid}")
async def update_calc_report_share(
    shareOid: str,
    request: ShareLinkCreateDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[ShareLinkResDTO]:
    """Replace settings for one active share link owned by the current user."""
    return ok(
        data=await calc_report_share_service.update_share_link(
            tokenPayloads.id, shareOid, request, session
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
@allow_anonymous
async def preview_shared_calc_report(
    token: str,
    tokenPayloads: TokenPayloads | None = Depends(get_optional_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[SharePreviewResDTO]:
    """Preview the authorized approved closure without consuming the link."""
    user_id = tokenPayloads.id if tokenPayloads is not None else None
    preview = await calc_report_share_service.preview_share(user_id, token, session)
    link, step = await calc_report_share_service.get_or_run_share_preview(
        user_id, token, session
    )
    if step.execution.resultPath:
        execution = execution_step_response(step)
    else:
        execution = await finalize_execution_step(
            step, None, link.createdByUserId, session
        )
    execution.htmlPath = f"/api/v1/calc-report/shared/{token}/result"
    preview.recentExecution = execution
    return ok(data=preview)


@router.get("/shared/{token}/result")
@allow_anonymous
async def get_shared_calc_report_result(
    token: str,
    tokenPayloads: TokenPayloads | None = Depends(get_optional_token_payload),
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Serve the share-specific default result after current access validation."""
    result_path = await calc_report_share_service.get_share_preview_result_path(
        tokenPayloads.id if tokenPayloads is not None else None, token, session
    )
    return FileResponse(result_path, media_type="text/html")


@router.get("/shared/{token}/archive")
@allow_anonymous
async def export_shared_calc_report(
    token: str,
    background_tasks: BackgroundTasks,
    tokenPayloads: TokenPayloads | None = Depends(get_optional_token_payload),
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Stream an authorized share as a portable v4 archive.

    Args:
        token: Share bearer token.
        background_tasks: FastAPI response cleanup queue.
        tokenPayloads: Optional authenticated recipient claims.
        session: Request database session.

    Returns:
        Streaming PNG archive response.

    Raises:
        CustomException: If the token is unavailable to the current recipient.
    """
    link, report, version = await calc_report_share_service._authorize_share(
        tokenPayloads.id if tokenPayloads is not None else None, token, session
    )
    await calc_report_share_service._consume_share(link, session)
    await session.commit()
    exported = await calc_report_archive_service.export_version_closure(
        report,
        version,
        can_edit=link.canEdit,
        can_share=link.canShare,
        session=session,
    )
    background_tasks.add_task(
        calc_report_archive_service.remove_exported_archive, exported
    )
    return FileResponse(
        exported.path,
        media_type="image/png",
        filename=exported.filename,
        background=background_tasks,
    )


@router.get("/shared/catalog/{shareOid}/archive")
async def export_catalog_shared_calc_report(
    shareOid: str,
    background_tasks: BackgroundTasks,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Stream an authorized same-backend catalog share as a v4 archive.

    Args:
        shareOid: Catalog share public identifier.
        background_tasks: FastAPI response cleanup queue.
        tokenPayloads: Authenticated user claims.
        session: Request database session.

    Returns:
        Streaming PNG archive response.

    Raises:
        CustomException: If the catalog share is unavailable to the user.
    """
    link = await session.scalar(
        select(CalcReportShareLink).where(CalcReportShareLink.oid == shareOid)
    )
    if link is None:
        from app.exception.custom_exception import raise_ex

        raise_ex("Share link is unavailable", code=404)
    link, report, version = await calc_report_share_service._authorize_share_link(
        tokenPayloads.id, link, session
    )
    await calc_report_share_service._consume_share(link, session)
    await session.commit()
    exported = await calc_report_archive_service.export_version_closure(
        report,
        version,
        can_edit=link.canEdit,
        can_share=link.canShare,
        session=session,
    )
    background_tasks.add_task(
        calc_report_archive_service.remove_exported_archive, exported
    )
    return FileResponse(
        exported.path,
        media_type="image/png",
        filename=exported.filename,
        background=background_tasks,
    )


@router.post("/shared/catalog/{shareOid}/import")
async def import_catalog_calc_report(
    shareOid: str,
    request: ShareImportDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[ShareImportResDTO]:
    """Import an accessible same-backend catalog entry."""
    return ok(
        data=await calc_report_share_service.import_catalog_share(
            tokenPayloads.id, shareOid, request, session
        )
    )


@router.get("/{reportOid}/sync")
async def get_calc_report_sync_status(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[ReportSyncResDTO]:
    """Check whether an owned synchronized report has an upstream update."""
    return ok(
        data=await calc_report_share_service.get_report_sync_status(
            tokenPayloads.id, reportOid, session
        )
    )


@router.post("/{reportOid}/sync")
async def synchronize_calc_report(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[ReportSyncResDTO]:
    """Atomically switch an owned synchronized report to upstream latest."""
    return ok(
        data=await calc_report_share_service.synchronize_report(
            tokenPayloads.id, reportOid, session
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
