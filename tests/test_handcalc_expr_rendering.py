"""Regression tests for rendering non-assignment expression statements."""

import html
import re

from core.uzoncalc import *


_record_once_call_count = 0


def _plain_text(content: str) -> str:
    """Convert rendered HTML/MathML into compact assertion text.

    Args:
        content: Rendered HTML or MathML content.

    Returns:
        Tag-stripped, HTML-unescaped text with spaces removed.

    Raises:
        No exceptions are intentionally raised.
    """
    return html.unescape(re.sub(r"<[^>]+>", "", content)).replace(" ", "")


def record_once_value() -> int:
    """Return a value while counting how often the expression is evaluated.

    Args:
        None.

    Returns:
        The integer value used by expression rendering tests.

    Raises:
        No exceptions are intentionally raised.
    """
    global _record_once_call_count
    _record_once_call_count += 1
    return 2


async def append_async_call_marker(ctx) -> int:
    """Append a marker while exercising a bare awaited call expression.

    Args:
        ctx: Active calculation context supplied by the caller.

    Returns:
        Marker value that should be ignored by bare-call expression handling.

    Raises:
        No exceptions are intentionally raised.
    """
    ctx.append_content("<p>await-call-side-effect</p>")
    return 1


@uzon_calc()
async def expression_result_sheet():
    """Render pure expression statements that should include final values.

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

    x / h_0
    x / h_0 < xi_b


@uzon_calc()
async def side_effect_expression_sheet():
    """Render an expression containing a function call exactly once.

    Args:
        None.

    Returns:
        None.

    Raises:
        No exceptions are intentionally raised.
    """
    base = 3
    record_once_value() + base


@uzon_calc()
async def table_expression_sheet():
    """Render a top-level table call without adding a formula row.

    Args:
        None.

    Returns:
        None.

    Raises:
        No exceptions are intentionally raised.
    """
    Table(["Name"], [["A"]])


@uzon_calc()
async def awaited_call_expression_sheet(ctx):
    """Execute a top-level awaited call without adding a formula row.

    Args:
        ctx: Active calculation context injected by ``@uzon_calc``.

    Returns:
        None.

    Raises:
        No exceptions are intentionally raised.
    """
    await append_async_call_marker(ctx)


def test_pure_division_expression_appends_final_result():
    """Pure division expression output includes original, substitution, and result.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: If the final runtime value is missing.
    """
    ctx = run_sync(expression_result_sheet)
    content = _plain_text(ctx.contents[-2])

    assert "xh0" in content
    assert "30mm100mm" in content
    assert content.endswith("=0.3")


def test_pure_comparison_expression_appends_final_result():
    """Pure comparison expression output includes original, substitution, and bool.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: If the final boolean result is missing.
    """
    ctx = run_sync(expression_result_sheet)
    content = _plain_text(ctx.contents[-1])

    assert "xh0<" in content
    assert "30mm100mm<0.5" in content
    assert content.endswith("=True")


def test_expression_with_function_call_runs_once_and_renders_result():
    """Expression capture preserves single evaluation for function calls.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: If the expression is re-evaluated or result is missing.
    """
    global _record_once_call_count
    _record_once_call_count = 0

    ctx = run_sync(side_effect_expression_sheet)
    content = _plain_text(ctx.contents[-1])

    assert _record_once_call_count == 1
    assert "record_once_value()+base" in content
    assert content.endswith("=5")


def test_top_level_table_call_does_not_render_formula_row():
    """Top-level Table calls keep their table side effect only.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: If the visitor records the Table call as a formula.
    """
    ctx = run_sync(table_expression_sheet)
    content = ctx.html_content()

    assert "<table" in content
    assert "<td>A</td>" in content
    assert "<math" not in content


def test_top_level_awaited_call_does_not_render_formula_row():
    """Top-level awaited calls keep side effects without formula output.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: If the awaited call is recorded as a formula.
    """
    ctx = run_sync(awaited_call_expression_sheet)
    content = ctx.html_content()

    assert "<p>await-call-side-effect</p>" in content
    assert "<math" not in content
