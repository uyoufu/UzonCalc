from __future__ import annotations

import ast
from typing import Callable

from .. import ir
from ..special_functions import format_special_function

ExprConverter = Callable[[ast.AST], ir.MathNode]
Unparser = Callable[[ast.AST], str]


def render_call(
    node: ast.Call,
    *,
    expr_to_ir: ExprConverter,
    unparse: Unparser,
) -> ir.MathNode:
    """渲染普通函数、方法调用以及特殊函数调用。"""
    args = [expr_to_ir(a) for a in node.args]

    # 尝试使用特殊函数格式化器
    special_formatted = format_special_function(unparse(node.func), args)
    if special_formatted is not None:
        return special_formatted

    # 处理方法调用如 b_f.to(unit.meter)
    if isinstance(node.func, ast.Attribute):
        obj = expr_to_ir(node.func.value)
        arg_nodes = build_call_arg_nodes(node, expr_to_ir=expr_to_ir)
        return ir.mrow(
            [
                obj,  # 对象，斜体
                ir.mo("."),  # 点号不是函数名，保持操作符样式
                ir.mfunction_name(node.func.attr),  # 方法名使用专用颜色
                ir.mo("("),
                *arg_nodes,  # 参数，斜体
                ir.mo(")"),
            ]
        )

    # 普通函数调用: f(a, b)
    arg_nodes = build_call_arg_nodes(node, expr_to_ir=expr_to_ir)
    return ir.mrow(
        [ir.mfunction_name(unparse(node.func)), ir.mo("("), *arg_nodes, ir.mo(")")]
    )


def build_call_arg_nodes(
    node: ast.Call,
    *,
    expr_to_ir: ExprConverter,
) -> list[ir.MathNode]:
    """统一渲染位置参数、关键字参数、星号参数。"""
    arg_nodes: list[ir.MathNode] = []
    call_args = [_call_arg_to_ir(arg, expr_to_ir) for arg in node.args]
    call_args.extend(_call_keyword_to_ir(keyword, expr_to_ir) for keyword in node.keywords)

    for idx, arg_node in enumerate(call_args):
        if idx:
            arg_nodes.append(ir.mo(","))
        arg_nodes.append(arg_node)

    return arg_nodes


def _call_arg_to_ir(node: ast.expr, expr_to_ir: ExprConverter) -> ir.MathNode:
    if isinstance(node, ast.Starred):
        return ir.mrow([ir.mo("*"), expr_to_ir(node.value)])
    return expr_to_ir(node)


def _call_keyword_to_ir(node: ast.keyword, expr_to_ir: ExprConverter) -> ir.MathNode:
    value_ir = expr_to_ir(node.value)
    if node.arg is None:
        return ir.mrow([ir.mo("**"), value_ir])
    return ir.mrow([ir.mtext(node.arg), ir.mo("="), value_ir])
