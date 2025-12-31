import ast

from core.handcalc.token_handlers.latex_writer import LaTeXWriter
from core.handcalc.record_step import record_step
from core.context import CalcContext


def _first_assign(src: str) -> ast.Assign:
    mod = ast.parse(src)
    for n in mod.body:
        if isinstance(n, ast.Assign):
            return n
    raise AssertionError("no Assign node found")


def test_subscript_name_and_format_safe_braces() -> None:
    node = _first_assign("a_b = x + 2")

    result = LaTeXWriter().format_assign(node)
    assert result is not None

    # Ensure subscript is represented using LaTeX braces, but escaped for str.format.
    assert "a_{{b}}" in (result.targets or "")

    full = f"{result.targets} = {result.latex} = {result.substitution}"
    rendered = full.format(**{"x": 3})

    assert "a_{b}" in rendered
    assert "3" in rendered


def test_pow_and_parentheses() -> None:
    node = _first_assign("y = (a + b) ** 2")
    result = LaTeXWriter().format_assign(node)
    assert result is not None

    full = f"{result.targets} = {result.latex} = {result.substitution}"
    rendered = full.format(**{"a": 1, "b": 2})

    # Display keeps expression structure.
    assert "(a + b)" in rendered
    assert "^" in rendered


def test_div_renders_frac_and_substitution() -> None:
    node = _first_assign("z = x / (a + b)")
    result = LaTeXWriter().format_assign(node)
    assert result is not None

    full = f"{result.targets} = {result.latex} = {result.substitution}"
    rendered = full.format(**{"x": 6, "a": 1, "b": 2})

    assert "\\frac" in rendered
    assert "6" in rendered
    assert "(1 + 2)" in rendered or "(a + b)" in rendered


def test_abs_renders_as_vertical_bars() -> None:
    node = _first_assign("y = abs(x)")
    result = LaTeXWriter().format_assign(node)
    assert result is not None

    assert result.latex == "\\left|x\\right|"
    assert result.substitution == "\\left|{x}\\right|"

    full = f"{result.targets} = {result.latex} = {result.substitution}"
    rendered = full.format(**{"x": -3})
    assert "\\left|-3\\right|" in rendered


def test_pint_unit_mult_renders_unit_name_only() -> None:
    node = _first_assign("pint_unit = 10 * unit.meter")
    result = LaTeXWriter().format_assign(node)
    assert result is not None

    assert result.latex == "10 meter"
    assert result.substitution == "10 meter"
    assert "{unit}" not in result.substitution


def test_record_step_omits_substitution_when_no_variables() -> None:
    ctx = CalcContext()
    record_step(ctx, name="a", expr="2", substitution="2", locals_map={"x": 3})
    assert ctx.contents[-1] == "a = 2"

    record_step(
        ctx,
        name="y",
        expr="x + 2",
        substitution="{x} + 2",
        locals_map={"x": 3},
    )
    assert ctx.contents[-1] == "y = x + 2 = 3 + 2"
