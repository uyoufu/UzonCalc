"""
桌面模式专用 API 控制器
"""

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.depends import get_session, get_token_payload
from app.exception.custom_exception import CustomException
from app.service import calc_report_service
from app.response.response_result import ResponseResult, ok, fail
from app.utils.show_dialog import show_file_dialog
from app.utils.file_explorer import show_in_file_explorer
from config import app_config
from utils.jwt_helper import TokenPayloads

router = APIRouter(
    prefix="/v1/desktop",
    tags=["desktop"],
)


@router.get("/select-file")
async def select_local_file() -> ResponseResult[str]:
    """
    弹出文件选择对话框并返回选择的文件路径（仅限桌面模式）
    """
    if not app_config.is_desktop:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only available in desktop mode",
        )

    try:
        # 使用 run_in_threadpool 避免阻塞 FastAPI 事件循环
        file_path = await run_in_threadpool(show_file_dialog)
        return ok(file_path if file_path else "")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to open file dialog: {str(e)}",
        )


@router.post("/calc-report/{report_oid}/show-in-explorer")
async def show_calc_report_in_explorer(
    report_oid: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """
    在文件资源管理器中显示计算报告源码文件（仅限桌面模式）
    """
    if not app_config.is_desktop:
        return fail(message="This endpoint is only available in desktop mode", code=403)

    file_path = await calc_report_service.get_calc_report_source_file_path(
        tokenPayloads.id,
        report_oid,
        session,
    )
    await run_in_threadpool(show_in_file_explorer, file_path)
    return ok()
