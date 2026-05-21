from __future__ import annotations

import ast
from typing import Callable

from .. import ir

Unparser = Callable[[ast.AST], str]


def render_subscript(node: ast.Subscript, *, unparse: Unparser) -> ir.MathNode:
    """渲染下标、切片和多维索引。"""
    base_name = _subscript_base_name(node.value, unparse)
    if base_name is None:
        return ir.mtext(unparse(node))

    sub_ir = _slice_to_ir(node.slice, unparse)
    return ir.msub(ir.mi(base_name), sub_ir)


def _subscript_base_name(node: ast.AST, unparse: Unparser) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return unparse(node)
    return None


def _slice_to_ir(node: ast.AST, unparse: Unparser) -> ir.MathNode:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return ir.mn(node.value)
        return ir.mtext(str(node.value))

    if isinstance(node, ast.Name):
        return ir.mi(node.id)

    if isinstance(node, ast.Tuple):
        parts: list[ir.MathNode] = []
        for idx, elt in enumerate(node.elts):
            if idx:
                parts.append(ir.mo(","))
            parts.append(_slice_to_ir(elt, unparse))
        return ir.mrow(parts)

    if isinstance(node, ast.Slice):
        parts: list[ir.MathNode] = []
        if node.lower is not None:
            parts.append(_slice_to_ir(node.lower, unparse))
        parts.append(ir.mo(":"))
        if node.upper is not None:
            parts.append(_slice_to_ir(node.upper, unparse))
        if node.step is not None:
            parts.append(ir.mo(":"))
            parts.append(_slice_to_ir(node.step, unparse))
        return ir.mrow(parts)

    return ir.mtext(unparse(node).replace(" ", ""))
