"""HTTP endpoints for complete calculation-report workspaces."""

import json
import mimetypes
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_state import BuildStatus
from app.controller.calc.calc_workspace_dto import (
    ReportDependencyDTO,
    WorkspaceBuildResDTO,
    WorkspaceDependenciesUpdateDTO,
    WorkspaceResDTO,
    WorkspaceSaveDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.exception.custom_exception import raise_ex
from app.response.response_result import ResponseResult, ok
from app.service import calc_report_workspace_service
from app.service.calc_report_build_service import get_build_state
from app.sandbox.core.backend_factory import get_sandbox_executor
from config import app_config
from utils.jwt_helper import TokenPayloads

router = APIRouter(prefix="/v1/calc-report", tags=["calc-report-workspace"])


@router.put("/{reportOid}/workspace")
async def save_calc_report_workspace(
    reportOid: str,
    snapshot: Annotated[str, Form()],
    files: Annotated[list[UploadFile] | None, File()] = None,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[WorkspaceResDTO]:
    """Replace a complete workspace using a multipart snapshot.

    Args:
        reportOid: Existing or client-preallocated report OID.
        snapshot: JSON-serialized WorkspaceSaveDTO.
        files: Uploaded files whose filenames equal workspace-relative paths.
        tokenPayloads: Authenticated user token.
        session: Database session.

    Returns:
        Saved workspace metadata and derived states.
    """
    try:
        request = WorkspaceSaveDTO.model_validate_json(snapshot)
    except ValidationError as error:
        raise_ex(
            "Workspace snapshot is invalid",
            code=422,
            data=json.loads(error.json()),
            error_code=CalcErrorCode.WORKSPACE_INVALID,
        )
    uploads: dict[str, bytes] = {}
    for upload in files or []:
        if not upload.filename or upload.filename in uploads:
            raise_ex(
                "Workspace upload filename is missing or duplicated",
                code=400,
                error_code=CalcErrorCode.WORKSPACE_INVALID,
            )
        content = await upload.read(app_config.calc_report_max_file_size + 1)
        if len(content) > app_config.calc_report_max_file_size:
            raise_ex(
                "Workspace file is too large",
                code=413,
                data={"path": upload.filename},
                error_code=CalcErrorCode.WORKSPACE_INVALID,
            )
        uploads[upload.filename] = content
    result = await calc_report_workspace_service.save_workspace(
        tokenPayloads.id, reportOid, request, uploads, session
    )
    return ok(data=result)


@router.get("/{reportOid}/workspace")
async def get_calc_report_workspace(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[WorkspaceResDTO]:
    """Return current workspace metadata for an owned report."""
    result = await calc_report_workspace_service.get_workspace(
        tokenPayloads.id, reportOid, session
    )
    return ok(data=result)


@router.get("/{reportOid}/workspace/file", response_class=Response)
async def get_calc_report_workspace_file(
    reportOid: str,
    path: Annotated[str, Query(min_length=1)],
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Stream one current workspace file with a best-effort media type."""
    content = await calc_report_workspace_service.get_workspace_file(
        tokenPayloads.id, reportOid, path, session
    )
    media_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return Response(content=content, media_type=media_type)


@router.get("/{reportOid}/workspace/dependencies")
async def get_calc_report_workspace_dependencies(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[ReportDependencyDTO]]:
    """Return dependency declarations from the current SOURCE artifact."""
    workspace = await calc_report_workspace_service.get_workspace(
        tokenPayloads.id, reportOid, session
    )
    return ok(data=workspace.dependencies)


@router.put("/{reportOid}/workspace/dependencies")
async def replace_calc_report_workspace_dependencies(
    reportOid: str,
    request: WorkspaceDependenciesUpdateDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[WorkspaceResDTO]:
    """Replace dependencies using the workspace optimistic revision boundary."""
    workspace = await calc_report_workspace_service.replace_workspace_dependencies(
        tokenPayloads.id, reportOid, request, session
    )
    return ok(data=workspace)


@router.get("/{reportOid}/workspace/build")
async def get_calc_report_workspace_build(
    reportOid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[WorkspaceBuildResDTO]:
    """Return build state for the globally configured execution runtime."""
    report = await calc_report_workspace_service.get_owned_report(
        tokenPayloads.id, reportOid, session
    )
    if report.workspaceArtifactId is None:
        return ok(
            data=WorkspaceBuildResDTO(
                sourceArtifactHash=f"sha256:{report.workspaceHash}",
                buildStatus=BuildStatus.NOT_REQUESTED,
            )
        )
    runtime = await get_sandbox_executor().runtime_descriptor()
    status, diagnostics = await get_build_state(
        report.workspaceArtifactId, runtime.fingerprint, session
    )
    artifact = await session.get(
        calc_report_workspace_service.CalcReportArtifact,
        report.workspaceArtifactId,
    )
    if artifact is None:
        raise_ex(
            "Workspace artifact not found",
            code=500,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
    return ok(
        data=WorkspaceBuildResDTO(
            sourceArtifactHash=f"sha256:{artifact.contentHash}",
            runtimeFingerprint=runtime.fingerprint,
            buildStatus=status,
            diagnostics=diagnostics,
        )
    )
