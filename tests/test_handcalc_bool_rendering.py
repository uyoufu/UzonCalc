"""Regression tests for boolean runtime values in handcalc output."""

import html
import re

from core.uzoncalc import *
from core.uzoncalc.handcalc.rendering.value_renderer import (
    should_render_runtime_value,
    value_to_ir,
)


def _plain_text(content: str) -> str:
    """Convert HTML/MathML content into compact text for assertions.

    Args:
        content: Rendered HTML or MathML content.

    Returns:
        Tag-stripped, HTML-unescaped text with spaces removed.

    Raises:
        No exceptions are intentionally raised.
    """
    return html.unescape(re.sub(r"<[^>]+>", "", content)).replace(" ", "")


@uzon_calc()
async def bool_comparison_sheet():
    """Render a comparison assignment whose runtime result is boolean.

    Args:
        None.

    Returns:
        None.

    Raises:
        No exceptions are intentionally raised.
    """
    h_0 = 100 * unit.mm
    x = 30 * unit.mm
    xi_b = 0.5
    xi = x / h_0 < xi_b


def test_boolean_runtime_values_render_as_text_literals():
    """Boolean runtime values are renderable as True/False text literals.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: If booleans are skipped or rendered as numeric values.
    """
    assert should_render_runtime_value(True)
    assert should_render_runtime_value(False)

    true_mathml = value_to_ir(True).to_mathml_xml()
    false_mathml = value_to_ir(False).to_mathml_xml()

    assert "<mtext>True</mtext>" in true_mathml
    assert "<mtext>False</mtext>" in false_mathml
    assert "<mn>True</mn>" not in true_mathml
    assert "<mn>False</mn>" not in false_mathml


def test_comparison_assignment_appends_boolean_result():
    """Comparison assignments include substituted expression and final bool.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: If the boolean result is omitted from the equation.
    """
    ctx = run_sync(bool_comparison_sheet)
    content = _plain_text(ctx.contents[-1])

    assert "30mm100mm<0.5" in content
    assert content.endswith("=True")
