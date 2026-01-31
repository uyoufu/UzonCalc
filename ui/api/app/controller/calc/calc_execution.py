"""
计算执行 API 控制器

提供 HTTP 端点供前端调用。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.controller.calc.calc_dto import CalcExecutionReqDTO
from app.controller.depends import get_session, get_token_payload
from app.response.response_result import ResponseResult, ok
from app.sandbox.execution_result import ExecutionResult
from app.service.calc_execution_service import start_execution, continue_execution

from config import logger
from utils.jwt_helper import TokenPayloads

router = APIRouter(
    prefix="/v1/calc/execution",
    tags=["calc-execution"],
)


@router.post("/start")
async def start_calc_execution(
    data: CalcExecutionReqDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    db_session: AsyncSession = Depends(get_session),
) -> ResponseResult[ExecutionResult]:
    """
    开始调用计算执行
    """

    result = await start_execution(
        db_session,
        tokenPayloads.id,
        data.reportId,
        data.defaults or {},
        is_silent=data.isSilent,
    )

    return ok(result)


@router.post("/resume/{connectionId}")
async def resume_calc_execution(
    connectionId: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    db_session: AsyncSession = Depends(get_session),
) -> ResponseResult[ExecutionResult]:
    """
    恢复调用计算执行
    """

    result = await continue_execution(connectionId, {})
    return ok(result)
