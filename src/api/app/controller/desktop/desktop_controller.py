"""
桌面模式专用 API 控制器
"""

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.depends import get_session, get_token_payload
from app.i18n import _
from app.service import calc_report_service
from app.service.calc_report_workspace_service import get_owned_report
from app.service.calc_report_artifact_service import (
    ArtifactValidationError,
    normalize_workspace_path,
)
from app.controller.dto_base import BaseDTO
from app.exception.custom_exception import raise_ex
from app.response.response_result import ResponseResult, ok, fail
from app.utils.show_dialog import show_file_dialog
from app.utils.file_explorer import show_in_file_explorer
from config import app_config
from utils.jwt_helper import TokenPayloads

router = APIRouter(
    prefix="/v1/desktop",
    tags=["desktop"],
)


class WorkspaceRevealDTO(BaseDTO):
    """Select one normalized workspace-relative file or directory path."""

    path: str


@router.get("/select-file")
async def select_local_file() -> ResponseResult[str]:
    """
    弹出文件选择对话框并返回选择的文件路径（仅限桌面模式）
    """
    if not app_config.is_desktop:
        return fail(message="This endpoint is only available in desktop mode", code=403)
    try:
        # 使用 run_in_threadpool 避免阻塞 FastAPI 事件循环
        file_path = await run_in_threadpool(show_file_dialog)
        return ok(file_path if file_path else "")
    except Exception as e:
        return fail(
            message=_("Failed to select file: {error}").format(error=str(e)),
            code=500,
        )


@router.post("/calc-report/{report_oid}/show-in-explorer")
async def show_calc_report_in_explorer(
    report_oid: str,
    request: WorkspaceRevealDTO | None = None,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """
    在文件资源管理器中显示计算报告源码文件（仅限桌面模式）
    """
    if not app_config.is_desktop:
        return fail(message="This endpoint is only available in desktop mode", code=403)

    await get_owned_report(tokenPayloads.id, report_oid, session)
    workspace_root = calc_report_service.get_workspace_projection_path(
        tokenPayloads.id, report_oid
    )
    workspace_path = workspace_root
    if request is not None and request.path:
        try:
            relative_path = normalize_workspace_path(request.path)
        except ArtifactValidationError:
            raise_ex("Workspace path is invalid", code=400)
        workspace_path = (workspace_root / relative_path).resolve()
        if (
            not workspace_path.is_relative_to(workspace_root)
            or not workspace_path.exists()
        ):
            raise_ex("Workspace path not found", code=404)
    await run_in_threadpool(show_in_file_explorer, str(workspace_path))
    return ok()
