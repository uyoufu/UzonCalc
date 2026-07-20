"""Property-based checks for pure AST-to-MathIR conversion."""

from __future__ import annotations

import ast

from hypothesis import given
from hypothesis import strategies as st

from uzoncalc.handcalc.ast_to_ir import expr_to_ir


@given(st.integers(min_value=-10**9, max_value=10**9))
def test_integer_literal_round_trips_through_math_ir(value: int) -> None:
    """Integer literals should survive AST-to-MathIR rendering unchanged."""
    expression = ast.parse(str(value), mode="eval").body

    rendered = expr_to_ir(expression).to_mathml_xml()

    assert str(abs(value)) in rendered
