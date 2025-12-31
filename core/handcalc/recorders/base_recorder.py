import ast
from typing import Any


class BaseRecorder:
    def record(self, node: Any) -> ast.AST | list[ast.stmt]:
        raise NotImplementedError("Subclasses should implement this method.")
