"""HTTP endpoint for safe legacy ``.uzc`` compatibility imports."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_workspace_dto import WorkspaceResDTO
from app.controller.calc.calc_error import CalcErrorCode
from app.controller.depends import get_session, get_token_payload
from app.exception.custom_exception import raise_ex
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_import_service
from config import app_config
from utils.jwt_helper import TokenPayloads

router = APIRouter(prefix="/v1/calc-report", tags=["calc-report-import"])


@router.post("/imports/uzc")
async def import_uzc_calc_report(
    categoryOid: Annotated[str, Form()],
    name: Annotated[str, Form(min_length=1, max_length=100)],
    archive: Annotated[UploadFile, File()],
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[WorkspaceResDTO]:
    """Convert one uploaded legacy archive into an unpublished workspace."""
    if not archive.filename or not archive.filename.lower().endswith(".uzc"):
        raise_ex(
            "A .uzc archive is required",
            code=400,
            error_code=CalcErrorCode.ARCHIVE_INVALID,
        )
    archive_bytes = await archive.read(app_config.calc_report_max_total_size + 1)
    if len(archive_bytes) > app_config.calc_report_max_total_size:
        raise_ex(
            "UZC archive exceeds the upload limit",
            code=413,
            error_code=CalcErrorCode.ARCHIVE_INVALID,
        )
    return ok(
        data=await calc_report_import_service.import_uzc_archive(
            tokenPayloads.id,
            categoryOid,
            name,
            archive_bytes,
            session,
        )
    )
