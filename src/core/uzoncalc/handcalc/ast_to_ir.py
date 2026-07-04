from __future__ import annotations

import ast
from functools import singledispatch
from typing import List

from . import ir
from .converters.call_rendering import render_call
from .converters.operator_rendering import (
    BINOP_INFIX,
    BinOpChildSide,
    CMP_OPS,
    OperatorContext,
    UNARY_OPS,
    apply_operator_context_parentheses,
)
from .converters.subscript_rendering import render_subscript
from .converters.unit_product import try_render_unit_product_expr


def _unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


def target_to_ir(node: ast.AST) -> ir.MathNode:
    """将赋值目标转换为 MathIR。"""
    # Targets are often Name/Attribute/Subscript/Tuple/List/Starred.
    if isinstance(node, ast.Name):
        return ir.mi(node.id)

    # Fallback for complex targets: keep readable.
    return ir.mtext(_unparse(node))


@singledispatch
def expr_to_ir(node: ast.AST) -> ir.MathNode:
    """
    Convert a Python AST expression node into a Math IR node.

    使用 singledispatch 实现，支持扩展新的 AST 节点类型。
    """
    # 默认回退：对于未知类型，使用 unparse
    return ir.mtext(_unparse(node))


def _expr_to_ir_with_context(
    node: ast.AST, operator_context: OperatorContext | None = None
) -> ir.MathNode:
    """使用父算符上下文渲染表达式，并在必要时补充括号。"""
    node_ir = expr_to_ir(node)
    return apply_operator_context_parentheses(node, node_ir, operator_context)


@expr_to_ir.register(ast.Name)
def _expr_name(node: ast.Name) -> ir.MathNode:
    return ir.mi(node.id)


@expr_to_ir.register(ast.Constant)
def _expr_constant(node: ast.Constant) -> ir.MathNode:
    value = node.value
    if isinstance(value, (int, float)):
        return ir.mn(value)
    # 布尔值和 None 的统一处理
    return ir.mtext(str(value) if value is not None else "None")


@expr_to_ir.register(ast.UnaryOp)
def _expr_unary(node: ast.UnaryOp) -> ir.MathNode:
    symbol = UNARY_OPS.get(type(node.op))
    if symbol is None:
        return ir.mtext(_unparse(node))
    return ir.mrow([ir.mo(symbol), _expr_to_ir_with_context(node.operand)])


@expr_to_ir.register(ast.BinOp)
def _expr_binop(node: ast.BinOp) -> ir.MathNode:
    # 特殊处理单位表达式
    unit_product = try_render_unit_product_expr(
        node, expr_to_ir=_expr_to_ir_with_context
    )
    if unit_product is not None:
        return unit_product

    op_type = type(node.op)

    # 转换左右子节点，并根据操作符优先级补充必要括号
    left = _expr_to_ir_with_context(
        node.left, OperatorContext(op_type, BinOpChildSide.LEFT)
    )
    right = _expr_to_ir_with_context(
        node.right, OperatorContext(op_type, BinOpChildSide.RIGHT)
    )

    # 中缀操作符
    symbol = BINOP_INFIX.get(op_type)
    if symbol is not None:
        return ir.mrow([left, ir.mo(symbol), right])

    # 特殊操作符
    if op_type is ast.Div:
        return ir.mfrac(left, right)
    if op_type is ast.Pow:
        return ir.msup(left, right)
    return ir.mtext(_unparse(node))


@expr_to_ir.register(ast.BoolOp)
def _expr_boolop(node: ast.BoolOp) -> ir.MathNode:
    op = "∧" if isinstance(node.op, ast.And) else "∨"
    items: List[ir.MathNode] = []
    for idx, value in enumerate(node.values):
        if idx:
            items.append(ir.mo(op))
        items.append(_expr_to_ir_with_context(value))
    return ir.mrow(items)


@expr_to_ir.register(ast.Compare)
def _expr_compare(node: ast.Compare) -> ir.MathNode:
    items: List[ir.MathNode] = [_expr_to_ir_with_context(node.left)]
    for op, comparator in zip(node.ops, node.comparators):
        items.append(ir.mo(CMP_OPS.get(type(op), op.__class__.__name__)))
        items.append(_expr_to_ir_with_context(comparator))
    return ir.mrow(items)


@expr_to_ir.register(ast.Call)
def _expr_call(node: ast.Call) -> ir.MathNode:
    # 函数调用的参数、特殊函数和方法调用格式化拆到 converters/call_rendering.py
    return render_call(node, expr_to_ir=_expr_to_ir_with_context, unparse=_unparse)


@expr_to_ir.register(ast.List)
def _expr_list(node: ast.List) -> ir.MathNode:
    # 与运行期 list 值保持一致，避免同一行出现文本数组和结构化数组两种样式
    return _sequence_to_array(node.elts)


@expr_to_ir.register(ast.Tuple)
def _expr_tuple(node: ast.Tuple) -> ir.MathNode:
    # Keep consistent with runtime tuple rendering, which currently uses brackets.
    return _sequence_to_array(node.elts)


@expr_to_ir.register(ast.Attribute)
def _expr_attribute(node: ast.Attribute) -> ir.MathNode:
    # like unit.meter
    if isinstance(node.value, ast.Name) and node.value.id == "unit":
        return ir.mu(node.attr)

    # 处理链式调用如 b_f.to(unit.meter).magnitude
    # value 是 Call 时，这是一个字段访问
    if isinstance(node.value, ast.Call):
        # 字段名渲染为斜体
        return ir.mrow([_expr_to_ir_with_context(node.value), ir.mi(f".{node.attr}")])
    return ir.mi(_unparse(node))


@expr_to_ir.register(ast.Subscript)
def _expr_subscript(node: ast.Subscript) -> ir.MathNode:
    return render_subscript(node, unparse=_unparse)


def _sequence_to_array(elements: list[ast.expr]) -> ir.MathNode:
    """列表/元组按数组值样式渲染。"""
    items: List[ir.MathNode] = []
    for idx, element in enumerate(elements):
        if idx:
            items.append(ir.mo(","))
        items.append(_expr_to_ir_with_context(element))
    return ir.mrow_array([ir.mo("["), *items, ir.mo("]")])
