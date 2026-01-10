"""单位表达式收集器模块

负责从 AST 表达式树中提取单位及其幂次，并构建对应的 IR 节点。
"""

from __future__ import annotations

import ast
from typing import Optional

from core.units import unit
from . import ir


class UnitExpressionCollector:
    """收集单位表达式中的单位及其幂次

    遍历乘除法表达式树，识别形如 unit.meter * unit.second**-1 的单位表达式，
    将其转换为单一的单位 IR 节点。

    示例:
        >>> collector = UnitExpressionCollector()
        >>> # 假设 node 代表: 5 * unit.meter / unit.second
        >>> if collector.walk(node, +1):
        ...     unit_node = collector.build_unit_node()
    """

    def __init__(self) -> None:
        self.coeff: float = 1.0
        self.unit_powers: dict[str, float] = {}

    def add_unit(self, name: str, power: float) -> None:
        """添加单位及其幂次到字典中

        Args:
            name: 单位名称，如 "meter"
            power: 幂次，如 2 表示平方
        """
        prev = self.unit_powers.get(name, 0.0)
        new = prev + power
        # 如果幂次接近 0，则移除该单位
        if abs(new) < 1e-12:
            self.unit_powers.pop(name, None)
        else:
            self.unit_powers[name] = new

    def walk(self, n: ast.AST, sign: int) -> bool:
        """遍历 AST 节点，收集单位信息

        Args:
            n: AST 节点
            sign: 符号标记，+1 表示乘法，-1 表示除法

        Returns:
            是否成功解析为单位表达式
        """
        # 乘法：递归处理左右子树
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult):
            return self.walk(n.left, sign) and self.walk(n.right, sign)

        # 除法：左边符号不变，右边符号取反
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
            return self.walk(n.left, sign) and self.walk(n.right, -sign)

        # unit.xxx 形式的单位
        if self._is_unit_attribute(n):
            self.add_unit(n.attr, float(sign))  # type: ignore
            return True

        # unit.xxx ** k 形式的幂次
        if self._is_unit_power(n):
            exp = get_const_number(n.right)  # type: ignore
            if exp is None:
                return False
            self.add_unit(n.left.attr, float(sign) * float(exp))  # type: ignore
            return True

        # 数值常量
        num = get_const_number(n)
        if num is not None:
            # 除数为 0 的情况
            if sign == -1 and float(num) == 0.0:
                return False
            self.coeff = (
                self.coeff * float(num) if sign == 1 else self.coeff / float(num)
            )
            return True

        return False

    @staticmethod
    def _is_unit_attribute(n: ast.AST) -> bool:
        """检查是否为 unit.xxx 形式"""
        return (
            isinstance(n, ast.Attribute)
            and isinstance(n.value, ast.Name)
            and n.value.id == "unit"
        )

    @staticmethod
    def _is_unit_power(n: ast.AST) -> bool:
        """检查是否为 unit.xxx ** k 形式"""
        return (
            isinstance(n, ast.BinOp)
            and isinstance(n.op, ast.Pow)
            and isinstance(n.left, ast.Attribute)
            and isinstance(n.left.value, ast.Name)
            and n.left.value.id == "unit"
        )

    def build_unit_node(self) -> ir.MathNode:
        """根据收集的信息构建单位 IR 节点

        Returns:
            表示单位表达式的 MathNode
        """
        units = unit.parse_units(unit_powers_to_expr(self.unit_powers))
        unit_node: ir.MathNode = ir.mu(str(units))

        # 系数为 1 时直接输出单位表达式
        coeff_node = number_to_mn(self.coeff)
        if coeff_node.value == "1":
            return unit_node

        return ir.mrow([coeff_node, ir.mo(""), unit_node])


# 辅助函数


def get_const_number(node: ast.AST) -> Optional[float]:
    """从 AST 节点中提取常量数值

    支持：
    - ast.Constant: 直接数值常量
    - ast.UnaryOp: 带符号的数值常量，如 -2

    Args:
        node: AST 节点

    Returns:
        提取的数值，如果不是常量则返回 None
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)

    # 处理 unit.m**-2 这类指数：UnaryOp(USub, Constant)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        inner = get_const_number(node.operand)
        if inner is None:
            return None
        return inner if isinstance(node.op, ast.UAdd) else -inner

    return None


def number_to_mn(value: float) -> ir.Mn:
    """将数值转换为 MathML 数字节点

    Args:
        value: 数值

    Returns:
        Mn 节点，整数用整数表示，浮点数保留小数
    """
    if float(value).is_integer():
        return ir.mn(int(value))
    return ir.mn(value)


def unit_powers_to_expr(unit_powers: dict[str, float]) -> str:
    """将单位及其幂次字典转换为字符串表达式

    Args:
        unit_powers: 单位名称到幂次的映射

    Returns:
        单位表达式字符串

    示例:
        >>> unit_powers_to_expr({'meter': 2, 'second': -1})
        'meter**2*second**-1'
    """
    return "*".join(
        f"{name}**{power}" if power != 1 else name
        for name, power in unit_powers.items()
    )
