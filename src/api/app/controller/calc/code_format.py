from fastapi import APIRouter

from app.controller.calc.code_format_dto import (
    PythonRuffFormatReqDTO,
    PythonRuffFormatResDTO,
)
from app.response.response_result import ResponseResult, ok
from app.service import code_format_service

router = APIRouter(
    prefix="/v1/code-format",
    tags=["code-format"],
)


@router.post("/python/ruff")
async def format_python_with_ruff(
    data: PythonRuffFormatReqDTO,
) -> ResponseResult[PythonRuffFormatResDTO]:
    """Format Python source with the server's isolated Ruff formatter."""
    result = await code_format_service.format_python_with_ruff(data)
    return ok(data=result)
