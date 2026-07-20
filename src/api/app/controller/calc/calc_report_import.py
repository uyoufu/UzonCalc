"""HTTP endpoints for portable report archive exports and imports."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_share_dto import (
    RemoteShareImportDTO,
    RemoteShareSourceDTO,
    ShareImportDTO,
    ShareImportResDTO,
    SharePreviewResDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.db.models.calc_report_version import CalcReportVersion
from app.exception.custom_exception import raise_ex
from app.response.response_result import ResponseResult, ok
from app.service import (
    calc_report_archive_service,
    calc_report_share_service,
    remote_share_service,
)
from config import app_config
from utils.jwt_helper import TokenPayloads

router = APIRouter(prefix="/v1/calc-report", tags=["calc-report-archive"])


@router.post("/imports/link/preview")
async def preview_remote_calc_report_link(
    request: RemoteShareSourceDTO,
) -> ResponseResult[SharePreviewResDTO]:
    """Proxy one anonymous remote public-share preview through SSRF controls.

    Args:
        request: Remote backend share URL.

    Returns:
        Validated remote preview metadata.

    Raises:
        CustomException: If the source is unsafe, private, or not public.
    """
    return ok(
        data=await remote_share_service.fetch_remote_share_preview(request.source)
    )


@router.post("/imports/link/archive")
async def download_remote_calc_report_link(
    request: RemoteShareSourceDTO,
) -> Response:
    """Proxy one anonymous remote public-share archive through SSRF controls.

    Args:
        request: Remote backend share URL.

    Returns:
        Bounded portable archive bytes.

    Raises:
        CustomException: If the source is unsafe, unavailable, or too large.
    """
    archive_bytes, _canonical_source = await remote_share_service.fetch_remote_share_archive(
        request.source
    )
    return Response(content=archive_bytes, media_type="image/png")


@router.post("/imports/link")
async def import_remote_calc_report_link(
    request: RemoteShareImportDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[ShareImportResDTO]:
    """Import one remote public share through its portable archive endpoint.

    Args:
        request: Remote source and receiver-owned import metadata.
        tokenPayloads: Authenticated receiving user claims.
        session: Request database session.

    Returns:
        Imported root and closure metadata.

    Raises:
        CustomException: If remote access or archive validation fails.
    """
    archive_bytes, canonical_source = (
        await remote_share_service.fetch_remote_share_archive(request.source)
    )
    return ok(
        data=await calc_report_archive_service.import_archive_closure(
            tokenPayloads.id,
            ShareImportDTO(
                categoryOid=request.categoryOid,
                name=request.name,
                shouldSync=request.shouldSync,
            ),
            archive_bytes,
            session,
            sync_locator=canonical_source,
        )
    )


@router.get("/{reportOid}/archive")
async def export_calc_report_archive(
    reportOid: str,
    background_tasks: BackgroundTasks,
    versionName: Annotated[str | None, Query()] = None,
    canEdit: Annotated[bool, Query()] = False,
    canShare: Annotated[bool, Query()] = False,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Stream an owned published version and its dependency closure.

    Args:
        reportOid: Owned report public identifier.
        background_tasks: FastAPI response cleanup queue.
        versionName: Optional semantic version; latest is used when omitted.
        canEdit: Whether importers may edit the exported report.
        canShare: Whether importers may create further shares.
        tokenPayloads: Authenticated user claims.
        session: Request database session.

    Returns:
        Streaming PNG archive response.

    Raises:
        CustomException: If the report has no selected published version.
    """
    report = await calc_report_share_service._get_owned_report(
        tokenPayloads.id, reportOid, session
    )
    if versionName:
        version = await calc_report_share_service._get_version(
            report, versionName, session
        )
    elif report.latestVersionId is not None:
        version = await session.get(CalcReportVersion, report.latestVersionId)
    else:
        version = None
    if version is None:
        raise_ex("Report has no published version", code=409)
    exported = await calc_report_archive_service.export_version_closure(
        report,
        version,
        can_edit=canEdit,
        can_share=canShare,
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


@router.post("/imports/archive")
async def import_calc_report_archive(
    categoryOid: Annotated[str, Form()],
    archive: Annotated[UploadFile, File()],
    name: Annotated[str | None, Form(max_length=100)] = None,
    shouldSync: Annotated[bool, Form()] = False,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[ShareImportResDTO]:
    """Import one validated v3 PNG or UZC report closure.

    Args:
        categoryOid: Receiver-owned category identifier.
        name: Optional root report display name.
        shouldSync: Reserved false value for file imports.
        archive: Uploaded v3 container.
        tokenPayloads: Authenticated user claims.
        session: Request database session.

    Returns:
        Imported root and closure metadata.

    Raises:
        CustomException: If the upload extension, size, or sync mode is invalid.
    """
    if not archive.filename or not archive.filename.lower().endswith((".png", ".uzc")):
        raise_ex(
            "A .png or .uzc archive is required",
            code=400,
            error_code=CalcErrorCode.ARCHIVE_INVALID,
        )
    if shouldSync:
        raise_ex("File imports cannot be synchronized", code=400)
    archive_bytes = await archive.read(app_config.calc_report_max_total_size + 1)
    if len(archive_bytes) > app_config.calc_report_max_total_size:
        raise_ex(
            "Report archive exceeds the upload limit",
            code=413,
            error_code=CalcErrorCode.ARCHIVE_INVALID,
        )
    return ok(
        data=await calc_report_archive_service.import_archive_closure(
            tokenPayloads.id,
            ShareImportDTO(categoryOid=categoryOid, name=name, shouldSync=False),
            archive_bytes,
            session,
        )
    )
