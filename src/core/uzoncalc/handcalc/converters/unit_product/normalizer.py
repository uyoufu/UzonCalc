"""Normalize multiplicative AST expressions into source-ordered factors."""

from __future__ import annotations

import ast
from fractions import Fraction

from .model import ExprFactor, NormalizedProduct, ProductFactor, UnitFactor


def normalize_unit_product(node: ast.AST) -> NormalizedProduct | None:
    """Normalize a multiplicative AST expression while preserving source order."""

    if not isinstance(node, ast.BinOp):
        return None

    factors = _collect_product_factors(node, Fraction(1))
    if factors is None:
        return None

    has_unit_factor = any(isinstance(factor, UnitFactor) for factor in factors)
    if not has_unit_factor:
        return None
    return NormalizedProduct(tuple(_drop_zero_power_factors(factors)))


def _collect_product_factors(
    node: ast.AST, power: Fraction
) -> list[ProductFactor] | None:
    """Collect ordered factors for multiplication, division, and constant powers."""

    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Mult):
            left_factors = _collect_product_factors(node.left, power)
            right_factors = _collect_product_factors(node.right, power)
            if left_factors is None or right_factors is None:
                return None
            return [*left_factors, *right_factors]

        if isinstance(node.op, ast.Div):
            left_factors = _collect_product_factors(node.left, power)
            right_factors = _collect_product_factors(node.right, -power)
            if left_factors is None or right_factors is None:
                return None
            return [*left_factors, *right_factors]

        if isinstance(node.op, ast.Pow):
            exponent = _get_const_fraction(node.right)
            if exponent is not None:
                return _collect_product_factors(node.left, power * exponent)

    unit_name = _unit_attribute_name(node)
    if unit_name is not None:
        return [UnitFactor(unit_name, power)]

    return [ExprFactor(node, power)]


def _drop_zero_power_factors(factors: list[ProductFactor]) -> list[ProductFactor]:
    """Remove factors whose power was cancelled by a zero exponent."""

    return [factor for factor in factors if factor.power != 0]


def _unit_attribute_name(node: ast.AST) -> str | None:
    """Return the unit name for a static ``unit.xxx`` AST node."""

    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "unit"
    ):
        return node.attr
    return None


def _get_const_fraction(node: ast.AST) -> Fraction | None:
    """Read an integer or finite decimal constant as an exact fraction."""

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Fraction(str(node.value))

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _get_const_fraction(node.operand)
        if value is None:
            return None
        return value if isinstance(node.op, ast.UAdd) else -value

    return None
