from enum import Enum
from dataclasses import dataclass


class ExecutionStatus(str, Enum):
    RUNNING = "running"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionResult:
    execution_id: str
    status: ExecutionStatus
    result: str | None = None
    ui_definition: dict | None = None
    error: str | None = None
