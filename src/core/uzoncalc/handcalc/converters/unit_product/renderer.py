"""Render unit-aware product display plans into MathIR."""

from __future__ import annotations

import ast
from collections.abc import Callable
from fractions import Fraction

from ....units import unit
from ... import ir
from ..operator_rendering import BinOpChildSide, OperatorContext
from .binding import build_product_display_plan
from .model import DisplayTerm, ProductDisplayPlan
from .normalizer import normalize_unit_product

ExprConverter = Callable[[ast.AST, OperatorContext | None], ir.MathNode]


def try_render_unit_product_expr(
    node: ast.AST, *, expr_to_ir: ExprConverter
) -> ir.MathNode | None:
    """Render a unit-aware multiplicative expression as MathIR."""

    product = normalize_unit_product(node)
    if product is None:
        return None

    plan = build_product_display_plan(product)
    return _render_display_plan(plan, expr_to_ir=expr_to_ir)


def _render_display_plan(
    plan: ProductDisplayPlan, *, expr_to_ir: ExprConverter
) -> ir.MathNode | None:
    """Convert a product display plan into existing MathIR nodes."""

    numerator_nodes = [
        _render_term(term, expr_to_ir=expr_to_ir) for term in plan.numerator_terms
    ]
    numerator_unit = _build_unit_node(plan.numerator_unit_powers)
    if numerator_unit is not None:
        numerator_nodes.append(numerator_unit)

    denominator_nodes = [
        _render_term(term, expr_to_ir=expr_to_ir) for term in plan.denominator_terms
    ]
    denominator_unit = _build_unit_node(plan.denominator_unit_powers)
    if denominator_unit is not None:
        denominator_nodes.append(denominator_unit)

    numerator = _render_product_nodes(numerator_nodes)
    denominator = _render_product_nodes(denominator_nodes)

    if numerator is None and denominator is None:
        return ir.mn(1)
    if denominator is None:
        return numerator
    return ir.mfrac(numerator or ir.mn(1), denominator)


def _render_term(term: DisplayTerm, *, expr_to_ir: ExprConverter) -> ir.MathNode:
    """Render one expression term and its locally attached unit powers."""

    expression_node = _render_expression_factor(term, expr_to_ir=expr_to_ir)
    unit_node = _build_unit_node(term.unit_powers)
    if unit_node is None:
        return expression_node
    return ir.mrow([expression_node, ir.mo(""), unit_node])


def _render_expression_factor(
    term: DisplayTerm, *, expr_to_ir: ExprConverter
) -> ir.MathNode:
    """Render an expression factor, adding a power when normalization requires it."""

    if term.power == 1:
        return expr_to_ir(term.node, OperatorContext(ast.Mult, BinOpChildSide.RIGHT))

    base = expr_to_ir(term.node, None)
    return ir.msup(base, _fraction_to_ir(term.power))


def _render_product_nodes(nodes: list[ir.MathNode]) -> ir.MathNode | None:
    """Join renderable factors with multiplication dots."""

    if not nodes:
        return None

    children: list[ir.MathNode] = []
    for idx, node in enumerate(nodes):
        if idx:
            children.append(ir.mo("·"))
        children.append(node)

    if len(children) == 1:
        return children[0]
    return ir.mrow(children)


def _build_unit_node(unit_powers: dict[str, Fraction]) -> ir.MathNode | None:
    """Build a single unit node from accumulated unit powers."""

    normalized_powers = {
        unit_name: unit_power
        for unit_name, unit_power in unit_powers.items()
        if unit_power != 0
    }
    if not normalized_powers:
        return None

    units = unit.parse_units(_unit_powers_to_expr(normalized_powers))
    return ir.mu(str(units))


def _unit_powers_to_expr(unit_powers: dict[str, Fraction]) -> str:
    """Convert unit powers to a pint-compatible unit expression."""

    return "*".join(
        _unit_power_to_expr(unit_name, unit_power)
        for unit_name, unit_power in unit_powers.items()
    )


def _unit_power_to_expr(unit_name: str, unit_power: Fraction) -> str:
    """Convert one unit power to a pint-compatible factor expression."""

    if unit_power == 1:
        return unit_name
    if unit_power.denominator == 1:
        return f"{unit_name}**{unit_power.numerator}"
    return f"{unit_name}**{float(unit_power)}"


def _fraction_to_ir(value: Fraction) -> ir.MathNode:
    """Render a normalized expression power."""

    if value.denominator == 1:
        return ir.mn(value.numerator)
    return ir.mfrac(ir.mn(value.numerator), ir.mn(value.denominator))
