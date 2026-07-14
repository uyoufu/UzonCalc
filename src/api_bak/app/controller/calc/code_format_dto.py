from app.controller.dto_base import BaseDTO


class PythonBlackFormatReqDTO(BaseDTO):
    code: str
    lineLength: int = 88


class PythonBlackFormatResDTO(BaseDTO):
    formattedCode: str
    changed: bool
    formatter: str = "black"
