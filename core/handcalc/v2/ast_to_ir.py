from __future__ import annotations

import ast
from typing import Any, List, Optional
from core.units import unit
from pint.util import UnitsContainer
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
        folded = _try_fold_unit_expr_as_single_mu(node)
        if folded is not None:
            return folded

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
        items: List[ir.MathNode] = []
        for idx, v in enumerate(node.values):
            if idx:
                items.append(ir.mo(op))
            items.append(expr_to_ir(v))
        return ir.mrow(items)

    # Compare
    if isinstance(node, ast.Compare):
        items: List[ir.MathNode] = [expr_to_ir(node.left)]
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
        # NOTE: avoid <mfenced> for better MathML Core compatibility (some renderers
        # drop mfenced parentheses). Emit explicit '(' and ')' operators instead.
        arg_nodes: List[ir.MathNode] = []
        for idx, a in enumerate(args):
            if idx:
                arg_nodes.append(ir.mo(","))
            arg_nodes.append(a)

        return ir.mrow([ir.mtext(func_name), ir.mo("("), *arg_nodes, ir.mo(")")])

    # Attribute
    # like unit.meter
    if isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name) and node.value.id == "unit":
            return ir.mu(node.attr)
        else:
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


def _try_fold_unit_expr_as_single_mu(node: ast.AST) -> Optional[ir.MathNode]:
    """
    遍历乘除法表达式树，提取出其中的单位及其幂次，构造一个单一的 ir.Mu 节点表示该单位表达式
    若没有符合的单位乘除法表达式，返回 None
    """

    if not isinstance(node, ast.BinOp) or not isinstance(
        node.op, (ast.Mult, ast.Div, ast.Pow)
    ):
        return None

    coeff: float = 1.0
    unit_powers: dict[str, float] = {}

    def add_unit(name: str, power: float) -> None:
        """
        添加单位及其幂次到字典中
        """
        prev = unit_powers.get(name, 0.0)
        new = prev + power
        if abs(new) < 1e-12:
            unit_powers.pop(name, None)
        else:
            unit_powers[name] = new

    def walk(n: ast.AST, sign: int) -> bool:
        nonlocal coeff

        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult):
            return walk(n.left, sign) and walk(n.right, sign)

        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
            return walk(n.left, sign) and walk(n.right, -sign)

        # unit.xxx
        if (
            isinstance(n, ast.Attribute)
            and isinstance(n.value, ast.Name)
            and n.value.id == "unit"
        ):
            add_unit(n.attr, float(sign))
            return True

        # unit.xxx ** k
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow):
            if (
                isinstance(n.left, ast.Attribute)
                and isinstance(n.left.value, ast.Name)
                and n.left.value.id == "unit"
            ):
                exp = _get_const_number(n.right)
                if exp is None:
                    return False
                add_unit(n.left.attr, float(sign) * float(exp))
                return True
            return False

        # numeric constant
        num = _get_const_number(n)
        if num is not None:
            if sign == -1 and float(num) == 0.0:
                return False
            coeff = coeff * float(num) if sign == 1 else coeff / float(num)
            return True

        return False

    if not walk(node, +1):
        return None

    if not unit_powers:
        return None

    units = unit.parse_units(_unit_powers_to_unit_expr(unit_powers))
    unit_node: ir.MathNode = ir.mu(str(units))

    # 系数为 1 时直接输出单位表达式
    coeff_node = _number_to_mn(coeff)
    if coeff_node.value == "1":
        return unit_node

    return ir.mrow([coeff_node, ir.mo(""), unit_node])


def _get_const_number(node: ast.AST) -> Optional[float]:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)

    # 处理 unit.m**-2 这类指数：UnaryOp(USub, Constant)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        inner = _get_const_number(node.operand)
        if inner is None:
            return None
        return inner if isinstance(node.op, ast.UAdd) else -inner

    return None


def _number_to_mn(value: float) -> ir.Mn:
    if float(value).is_integer():
        return ir.mn(int(value))
    return ir.mn(value)


def _unit_powers_to_unit_expr(unit_powers: dict[str, float]) -> str:
    """
    将单位及其幂次字典转换为字符串表达式
    例如: {'meter': 2, 'second': -1} -> "meter**2/second"
    """

    return "*".join(
        f"{name}**{power}" if power != 1 else name
        for name, power in unit_powers.items()
    )
