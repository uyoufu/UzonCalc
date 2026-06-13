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


@uzon_calc()
async def calc_f_string_table_reference():
    table_ref = Table(["Name"], [["A"]], title="示例表")
    f"A < B 的引用为 {table_ref} > C"


@uzon_calc()
async def calc_f_string_raw_html_string():
    raw_html = '<span data-raw="true"></span>'
    f"raw {raw_html}"


@uzon_calc()
async def calc_f_string_equation_table_reference():
    enable_fstring_equation()
    table_ref = Table(["Name"], [["A"]], title="示例表")
    f"见 {table_ref}"


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


def test_f_string_renders_table_reference_as_html_fragment():
    ctx = run_sync(calc_f_string_table_reference)
    content = ctx.contents[-1]

    assert "A &lt; B 的引用为 " in content
    assert (
        '<span data-uzoncalc-label-ref="table-1" data-uzoncalc-label-kind="table" data-uzoncalc-label-prefix="表"></span>'
        in content
    )
    assert " &gt; C" in content
    assert "&lt;span" not in content


def test_f_string_escapes_raw_html_string():
    ctx = run_sync(calc_f_string_raw_html_string)
    content = ctx.contents[-1]

    assert '&lt;span data-raw=&quot;true&quot;&gt;&lt;/span&gt;' in content
    assert '<span data-raw="true"></span>' not in content


def test_f_string_equation_mode_keeps_table_reference_as_html_fragment():
    ctx = run_sync(calc_f_string_equation_table_reference)
    content = ctx.contents[-1]

    assert "见 " in content
    assert (
        '<span data-uzoncalc-label-ref="table-1" data-uzoncalc-label-kind="table" data-uzoncalc-label-prefix="表"></span>'
        in content
    )
    assert "<math" not in content


if __name__ == "__main__":
    ctx = run_sync(test_f_string)
    print(ctx.contents)
    assert all("MText(text=" not in item for item in ctx.contents)

    ctx = run_sync(calc_f_string_formatted_unit)
    print(ctx.contents)
    assert 'class="unit"' in ctx.contents[-1]
