import black

from app.controller.calc.code_format_dto import (
    PythonBlackFormatReqDTO,
    PythonBlackFormatResDTO,
)
from app.exception.custom_exception import raise_ex
from config import logger


async def format_python_with_black(
    data: PythonBlackFormatReqDTO,
) -> PythonBlackFormatResDTO:
    """
    使用 Black 格式化 Python 代码
    """
    line_length = data.lineLength
    if line_length <= 0:
        raise_ex("lineLength must be greater than 0", code=400)

    mode = black.Mode(line_length=line_length)

    try:
        formatted = black.format_file_contents(
            data.code,
            fast=False,
            mode=mode,
        )
        return PythonBlackFormatResDTO(formattedCode=formatted, changed=True)
    except black.NothingChanged:
        return PythonBlackFormatResDTO(formattedCode=data.code, changed=False)
    except black.InvalidInput as ex:
        raise_ex(f"Black format failed: {ex}", code=400)
    except Exception as ex:
        logger.error(f"Unexpected Black formatting error: {ex}", exc_info=True)
        raise_ex("Python formatting failed", code=500)
