from core.uzoncalc import *


@uzon_calc()
async def test_f_string():
    pi = 3.1415926535
    f"Value of pi up to 3 decimal places: {pi:.3f}"


@uzon_calc()
async def calc_f_string_formatted_unit():
    length = 1.234 * unit.meter
    f"length: {length:.2f}"


@uzon_calc()
async def calc_f_string_unformatted_unit():
    length = 1.234 * unit.meter
    f"length: {length}"


@uzon_calc()
async def calc_f_string_equation_formatted_unit():
    enable_fstring_equation()
    length = 1.234 * unit.meter
    f"length: {length:.2f}"


def test_f_string_formats_unit_as_mathml_fragment():
    ctx = run_sync(calc_f_string_formatted_unit)
    content = ctx.contents[-1]

    assert "1.23" in content
    assert 'class="unit"' in content
    assert ">m<" in content
    assert "MRow(children=" not in content
    assert "Mu(name=" not in content


def test_f_string_unformatted_unit_as_mathml_fragment():
    ctx = run_sync(calc_f_string_unformatted_unit)
    content = ctx.contents[-1]

    assert "1.234" in content
    assert 'class="unit"' in content
    assert ">m<" in content
    assert "MRow(children=" not in content


def test_f_string_equation_formatted_unit_keeps_unit_class():
    ctx = run_sync(calc_f_string_equation_formatted_unit)
    content = ctx.contents[-1]

    assert "1.23" in content
    assert 'class="unit"' in content
    assert ">m<" in content
    assert "MRow(children=" not in content


if __name__ == "__main__":
    ctx = run_sync(test_f_string)
    print(ctx.contents)
    assert all("MText(text=" not in item for item in ctx.contents)

    ctx = run_sync(calc_f_string_formatted_unit)
    print(ctx.contents)
    assert 'class="unit"' in ctx.contents[-1]
