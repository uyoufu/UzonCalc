"""Bind normalized unit factors to nearby expression factors."""

from __future__ import annotations

from fractions import Fraction

from .model import (
    DisplayTerm,
    ExprFactor,
    NormalizedProduct,
    ProductDisplayPlan,
    ProductFactor,
    UnitFactor,
)


def build_product_display_plan(product: NormalizedProduct) -> ProductDisplayPlan:
    """Bind unit factors to expression factors within numerator/denominator sides."""

    if not product.has_expr_factor:
        return ProductDisplayPlan(
            numerator_unit_powers=_collect_signed_unit_powers(product.factors),
        )

    numerator_factors = _select_side_factors(product.factors, +1)
    denominator_factors = _select_side_factors(product.factors, -1)
    numerator_terms, numerator_units = _bind_side_factors(numerator_factors)
    denominator_terms, denominator_units = _bind_side_factors(denominator_factors)

    numerator_units, denominator_units = _merge_unit_only_denominator_when_readable(
        numerator_terms,
        numerator_units,
        denominator_terms,
        denominator_units,
    )

    return ProductDisplayPlan(
        numerator_terms=tuple(numerator_terms),
        denominator_terms=tuple(denominator_terms),
        numerator_unit_powers=numerator_units,
        denominator_unit_powers=denominator_units,
    )


def _select_side_factors(
    factors: tuple[ProductFactor, ...], side: int
) -> list[ProductFactor]:
    """Keep factors that belong to the requested product side."""

    selected: list[ProductFactor] = []
    for factor in factors:
        if side > 0 and factor.power > 0:
            selected.append(factor)
        elif side < 0 and factor.power < 0:
            selected.append(_with_positive_power(factor))
    return selected


def _with_positive_power(factor: ProductFactor) -> ProductFactor:
    """Convert a denominator factor to its positive display power."""

    if isinstance(factor, ExprFactor):
        return ExprFactor(factor.node, -factor.power)
    return UnitFactor(factor.name, -factor.power)


def _bind_side_factors(
    factors: list[ProductFactor],
) -> tuple[list[DisplayTerm], dict[str, Fraction]]:
    """Attach side-local unit runs to adjacent expression terms."""

    terms: list[DisplayTerm] = []
    leading_units: dict[str, Fraction] = {}
    standalone_units: dict[str, Fraction] = {}

    for factor in factors:
        if isinstance(factor, UnitFactor):
            target_units = terms[-1].unit_powers if terms else leading_units
            _add_unit_power(target_units, factor.name, factor.power)
            continue

        term_units = dict(leading_units)
        leading_units.clear()
        terms.append(DisplayTerm(factor.node, factor.power, term_units))

    if terms:
        return terms, standalone_units

    standalone_units.update(leading_units)
    return terms, standalone_units


def _collect_signed_unit_powers(
    factors: tuple[ProductFactor, ...],
) -> dict[str, Fraction]:
    """Collect signed powers for a pure-unit expression."""

    unit_powers: dict[str, Fraction] = {}
    for factor in factors:
        if isinstance(factor, UnitFactor):
            _add_unit_power(unit_powers, factor.name, factor.power)
    return unit_powers


def _merge_unit_only_denominator_when_readable(
    numerator_terms: list[DisplayTerm],
    numerator_units: dict[str, Fraction],
    denominator_terms: list[DisplayTerm],
    denominator_units: dict[str, Fraction],
) -> tuple[dict[str, Fraction], dict[str, Fraction]]:
    """Merge denominator units into the last quantity term when it has units already."""

    if (
        not denominator_terms
        and denominator_units
        and not numerator_units
        and numerator_terms
        and numerator_terms[-1].unit_powers
    ):
        target_units = numerator_terms[-1].unit_powers
        for unit_name, unit_power in denominator_units.items():
            _add_unit_power(target_units, unit_name, -unit_power)
        return numerator_units, {}

    return numerator_units, denominator_units


def _add_unit_power(
    unit_powers: dict[str, Fraction], name: str, power: Fraction
) -> None:
    """Accumulate unit powers and remove units whose power cancels to zero."""

    new_power = unit_powers.get(name, Fraction(0)) + power
    if new_power == 0:
        unit_powers.pop(name, None)
        return
    unit_powers[name] = new_power
