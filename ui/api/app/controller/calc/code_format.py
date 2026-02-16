from fastapi import APIRouter

from app.controller.calc.code_format_dto import (
    PythonBlackFormatReqDTO,
    PythonBlackFormatResDTO,
)
from app.response.response_result import ResponseResult, ok
from app.service import code_format_service

router = APIRouter(
    prefix="/v1/code-format",
    tags=["code-format"],
)


@router.post("/python/black")
async def format_python_with_black(
    data: PythonBlackFormatReqDTO,
) -> ResponseResult[PythonBlackFormatResDTO]:
    """
    使用 Black 格式化 Python 代码
    """
    result = await code_format_service.format_python_with_black(data)
    return ok(data=result)
