from __future__ import annotations

import ast
from typing import Any, List

from . import ir


def _unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


def target_to_ir(node: ast.AST) -> ir.MathNode:
    # Targets are often Name/Attribute/Subscript/Tuple/List/Starred.
    if isinstance(node, ast.Name):
        return ir.mi(node.id)

    # Fallback for complex targets: keep readable.
    return ir.mtext(_unparse(node))


def expr_to_ir(node: ast.AST) -> ir.MathNode:
    """
    Convert a Python AST expression node into a Math IR node.
    This is a best-effort conversion for common expressions.
    """

    # Basic atoms
    if isinstance(node, ast.Name):
        return ir.mi(node.id)

    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, (int, float)):
            return ir.mn(v)
        if isinstance(v, str):
            # As part of a math expression, treat as text.
            return ir.mtext(v)
        if v is None:
            return ir.mtext("None")
        if v is True:
            return ir.mtext("True")
        if v is False:
            return ir.mtext("False")
        return ir.mtext(str(v))

    # Unary
    if isinstance(node, ast.UnaryOp):
        operand = expr_to_ir(node.operand)
        if isinstance(node.op, ast.UAdd):
            return ir.mrow([ir.mo("+"), operand])
        if isinstance(node.op, ast.USub):
            return ir.mrow([ir.mo("-"), operand])
        if isinstance(node.op, ast.Not):
            return ir.mrow([ir.mo("not"), operand])
        if isinstance(node.op, ast.Invert):
            return ir.mrow([ir.mo("~"), operand])
        return ir.mtext(_unparse(node))

    # Binary
    if isinstance(node, ast.BinOp):
        # 判断后者是否为单位，若是单位，提取所有子 ast 节点，进行单位求值
        if isinstance(node.op, (ast.Mult, ast.Div, ast.Pow)):
            # 判断右侧是否为单位
            pass

        left = expr_to_ir(node.left)
        right = expr_to_ir(node.right)

        if isinstance(node.op, ast.Add):
            return ir.mrow([left, ir.mo("+"), right])
        if isinstance(node.op, ast.Sub):
            return ir.mrow([left, ir.mo("-"), right])
        if isinstance(node.op, ast.Mult):
            return ir.mrow([left, ir.mo("·"), right])
        if isinstance(node.op, ast.Div):
            return ir.mfrac(left, right)
        if isinstance(node.op, ast.FloorDiv):
            return ir.mrow([left, ir.mo("//"), right])
        if isinstance(node.op, ast.Mod):
            return ir.mrow([left, ir.mo("%"), right])
        if isinstance(node.op, ast.Pow):
            return ir.msup(left, right)

        return ir.mtext(_unparse(node))

    # BoolOp
    if isinstance(node, ast.BoolOp):
        op = "and" if isinstance(node.op, ast.And) else "or"
        items: List[ir.Math] = []
        for idx, v in enumerate(node.values):
            if idx:
                items.append(ir.mo(op))
            items.append(expr_to_ir(v))
        return ir.mrow(items)

    # Compare
    if isinstance(node, ast.Compare):
        items: List[ir.Math] = [expr_to_ir(node.left)]
        for op, comp in zip(node.ops, node.comparators):
            items.append(ir.mo(_cmp_op_to_str(op)))
            items.append(expr_to_ir(comp))
        return ir.mrow(items)

    # Call
    if isinstance(node, ast.Call):
        func_name = _unparse(node.func)
        args = [expr_to_ir(a) for a in node.args]

        # Special cases
        if func_name == "abs" and len(args) == 1:
            return ir.mrow([ir.mo("|"), args[0], ir.mo("|")])
        if func_name in ("sqrt", "math.sqrt") and len(args) == 1:
            return ir.msqrt(args[0])

        # Generic function call: f(a, b)
        arg_nodes: List[ir.Math] = []
        for idx, a in enumerate(args):
            if idx:
                arg_nodes.append(ir.mo(","))
            arg_nodes.append(a)

        return ir.mrow([ir.mtext(func_name), ir.mfenced(ir.mrow(arg_nodes))])

    # Attribute
    # like unit.meter
    if isinstance(node, ast.Attribute):
        # 将 unit.meter 转换为 {unit.meter} 以便后续处理
        return ir.mi(_unparse(node))

    # Subscript/Tuple/List/Dict/Set/etc.
    return ir.mtext(_unparse(node))


def _cmp_op_to_str(op: ast.cmpop) -> str:
    if isinstance(op, ast.Eq):
        return "="
    if isinstance(op, ast.NotEq):
        return "≠"
    if isinstance(op, ast.Lt):
        return "<"
    if isinstance(op, ast.LtE):
        return "≤"
    if isinstance(op, ast.Gt):
        return ">"
    if isinstance(op, ast.GtE):
        return "≥"
    if isinstance(op, ast.In):
        return "in"
    if isinstance(op, ast.NotIn):
        return "not in"
    if isinstance(op, ast.Is):
        return "is"
    if isinstance(op, ast.IsNot):
        return "is not"
    return op.__class__.__name__


def is_unit_multiplication_chain(node: ast.AST) -> bool:
    """
    判断节点是否为纯单位乘除法链。
    例如: unit.m**2 / unit.s 或 unit.kg * unit.m / unit.s**2
    """
    if isinstance(node, ast.BinOp):
        # 检查操作符是否为乘法或除法
        if not isinstance(node.op, (ast.Mult, ast.Div)):
            return False
        # 递归检查左右两侧
        return is_unit_multiplication_chain(node.left) and is_unit_multiplication_chain(
            node.right
        )

    elif isinstance(node, ast.Attribute):
        # 检查是否为 unit.xxx 形式
        if isinstance(node.value, ast.Name) and node.value.id == "unit":
            return True
        return False

    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
        # 允许幂运算，如 unit.m**2
        return is_unit_multiplication_chain(node.left)

    elif isinstance(node, ast.Constant):
        # 允许常量（如数字）
        return True

    return False


def is_pure_unit_expression(node: ast.AST) -> bool:
    """
    判断表达式是否为: 数字 * 单位乘除法链
    例如: 2.3e-6 * unit.m**8 / (unit.s**2 * unit.kg)
    """
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        # 左侧是数字，右侧是单位链
        left_is_number = isinstance(node.left, (ast.Constant, ast.Constant))
        right_is_units = is_unit_multiplication_chain(node.right)

        if left_is_number and right_is_units:
            return True

    return is_unit_multiplication_chain(node)
