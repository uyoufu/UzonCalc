"""Internal data structures for unit-aware product rendering."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class ExprFactor:
    """A non-unit expression factor in multiplicative normal form."""

    node: ast.AST
    power: Fraction


@dataclass(frozen=True, slots=True)
class UnitFactor:
    """A unit factor in multiplicative normal form."""

    name: str
    power: Fraction


ProductFactor = ExprFactor | UnitFactor


@dataclass(frozen=True, slots=True)
class NormalizedProduct:
    """Source-ordered product factors collected from a multiplication tree."""

    factors: tuple[ProductFactor, ...]

    @property
    def has_unit_factor(self) -> bool:
        """Return whether the product contains at least one static unit factor."""

        return any(isinstance(factor, UnitFactor) for factor in self.factors)

    @property
    def has_expr_factor(self) -> bool:
        """Return whether the product contains at least one non-unit factor."""

        return any(isinstance(factor, ExprFactor) for factor in self.factors)


@dataclass(frozen=True, slots=True)
class DisplayTerm:
    """A renderable expression term with locally attached units."""

    node: ast.AST
    power: Fraction = Fraction(1)
    unit_powers: dict[str, Fraction] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProductDisplayPlan:
    """A display plan split into numerator and denominator terms."""

    numerator_terms: tuple[DisplayTerm, ...] = ()
    denominator_terms: tuple[DisplayTerm, ...] = ()
    numerator_unit_powers: dict[str, Fraction] = field(default_factory=dict)
    denominator_unit_powers: dict[str, Fraction] = field(default_factory=dict)
