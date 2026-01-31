from app.controller.dto_base import BaseDTO


class ExecutionResult(BaseDTO):
    executionId: str
    window: dict
    html: str
    isCompleted: bool = False
