from __future__ import annotations

import ast
from typing import Any


def py_to_ast(obj: Any) -> ast.expr:
    """Convert a Python literal structure (dict/list/str/number/bool/None) into an AST expression."""

    if obj is None or isinstance(obj, (bool, int, float, str)):
        return ast.Constant(value=obj)

    if isinstance(obj, list):
        return ast.List(elts=[py_to_ast(v) for v in obj], ctx=ast.Load())

    if isinstance(obj, tuple):
        return ast.Tuple(elts=[py_to_ast(v) for v in obj], ctx=ast.Load())

    if isinstance(obj, dict):
        keys = []
        values = []
        for k, v in obj.items():
            if not isinstance(k, str):
                raise TypeError("Only string keys are supported for dict literals")
            keys.append(ast.Constant(value=k))
            values.append(py_to_ast(v))
        return ast.Dict(keys=keys, values=values)

    raise TypeError(f"Unsupported literal type for AST embedding: {type(obj)!r}")
