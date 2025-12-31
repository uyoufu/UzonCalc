import ast
from typing import Any


RecordedNode = ast.AST | list[ast.stmt]


class BaseRecorder:
    def record(self, node: Any) -> RecordedNode:
        raise NotImplementedError("Subclasses should implement this method.")
