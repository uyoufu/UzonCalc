import html
import re
from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from uzoncalc import run_sync, unit, uzon_calc
except ImportError:
    from uzoncalc.uzoncalc import run_sync, unit, uzon_calc


@dataclass(slots=True)
class RectangleSection:
    width: object
    height: object


def build_rectangle_section(width, height) -> RectangleSection:
    return RectangleSection(width=width, height=height)


def _plain_text(content: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", content))


@uzon_calc()
async def sub_function_sheet():
    width = 300 * unit.millimeter
    height = 500 * unit.millimeter
    section = build_rectangle_section(width=width, height=height)


@uzon_calc()
async def numeric_function_sheet():
    a = 1
    b = 2
    c = sum([a, b])


def test_sub_function_call_renders_runtime_keyword_arguments():
    ctx = run_sync(sub_function_sheet)
    section_line = _plain_text(ctx.contents[-1])

    assert "section=build_rectangle_section(width=width,height=height)" in section_line
    assert "build_rectangle_section(width=300mm,height=500mm)" in section_line
    assert "RectangleSection" not in section_line
    assert "Quantity" not in section_line


def test_numeric_function_call_still_renders_result_value():
    ctx = run_sync(numeric_function_sheet)
    result_line = _plain_text(ctx.contents[-1])

    assert "sum([a,b])" in result_line
    assert result_line.endswith("=3")
