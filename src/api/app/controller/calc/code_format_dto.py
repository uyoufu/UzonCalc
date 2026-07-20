from app.controller.dto_base import BaseDTO


class PythonRuffFormatReqDTO(BaseDTO):
    """Describe Python source formatting options for Ruff."""

    code: str
    lineLength: int = 88


class PythonRuffFormatResDTO(BaseDTO):
    """Return formatted Python source and whether Ruff changed it."""

    formattedCode: str
    changed: bool
    formatter: str = "ruff"
