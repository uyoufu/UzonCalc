"""
计算执行 API 控制器

提供 HTTP 端点供前端调用。
"""

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional

from app.controller.calc.calc_dto import (
    CalcExecutionReqDTO,
    CalcFileReqDTO,
    CalcResumeReqDTO,
    ExecutionResultResDTO,
)
from app.controller.depends import get_session, get_token_payload
from app.i18n import _
from app.response.response_result import ResponseResult, ok
from app.sandbox.core.execution_result import ExecutionResult
from app.service.calc_execution_service import (
    start_execution,
    continue_execution,
    start_file_execution,
)
from app.service.html_cache.html_cacher import html_cacher

from config import logger, app_config
from utils.jwt_helper import TokenPayloads

router = APIRouter(
    prefix="/v1/calc/execution",
    tags=["calc-execution"],
)


def finalize_execution_result_html(
    result: ExecutionResult, last_html_path: Optional[str], relative_path: str
) -> ExecutionResultResDTO:
    """整理执行结果 HTML 字段，转换为前端响应 DTO"""
    patch_result = html_cacher.build_content_patch_from_paths(
        last_html_path,
        relative_path,
    )

    res = ExecutionResultResDTO.model_validate(result)
    res.html = ""
    res.htmlPath = relative_path
    res.updateType = patch_result.updateType
    res.htmlContentPatch = patch_result.contentHtml
    return res


@router.post("/start")
async def start_calc_execution(
    data: CalcExecutionReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    db_session: AsyncSession = Depends(get_session),
) -> ResponseResult[ExecutionResultResDTO]:
    """
    开始调用计算执行
    """

    result = await start_execution(
        db_session,
        tokenPayloads.id,
        data.reportOid,
        data.defaults or {},
        is_silent=data.isSilent,
    )

    # 对结果进行缓存
    relative_path = await html_cacher.cache_html(result, tokenPayloads.id, db_session)
    response_dto = finalize_execution_result_html(
        result, data.lastHtmlPath, relative_path
    )

    return ok(response_dto)


@router.post("/resume/{connectionId}")
async def resume_calc_execution(
    connectionId: str,
    data: CalcResumeReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    db_session: AsyncSession = Depends(get_session),
) -> ResponseResult[ExecutionResultResDTO]:
    """
    恢复调用计算执行
    """

    result = await continue_execution(connectionId, data.defaults or {})

    # 对结果进行缓存
    relative_path = await html_cacher.cache_html(result, tokenPayloads.id, db_session)
    response_dto = finalize_execution_result_html(
        result, data.lastHtmlPath, relative_path
    )

    return ok(response_dto)


@router.post("/file")
async def start_file_calc_execution(
    data: CalcFileReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    db_session: AsyncSession = Depends(get_session),
) -> ResponseResult[ExecutionResultResDTO]:
    """
    启动文件执行（调试用）
    """
    if not app_config.is_desktop:
        raise HTTPException(
            status_code=403,
            detail=_("File execution is not allowed in server deployment"),
        )

    if not data.filePath:
        raise HTTPException(status_code=400, detail=_("filePath is required"))

    result = await start_file_execution(
        db_session, tokenPayloads.id, data.filePath, data.defaults or {}
    )

    # 对结果进行缓存
    relative_path = await html_cacher.cache_html(result, tokenPayloads.id, db_session)
    response_dto = finalize_execution_result_html(
        result, data.lastHtmlPath, relative_path
    )

    return ok(response_dto)
