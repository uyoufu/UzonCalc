import ast
import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from uzoncalc import run_sync, unit, uzon_calc
from uzoncalc.handcalc.ast_to_ir import expr_to_ir
from uzoncalc.handcalc.rendering.value_renderer import value_to_ir

MATHML_NAMESPACE = {"m": "http://www.w3.org/1998/Math/MathML"}
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MATH_STYLE_PATH = PROJECT_ROOT / "src/core/uzoncalc/template/js/src/styles/math.css"
CSS_COMMENT_PATTERN = re.compile(r"/\*.*?\*/", re.DOTALL)


@uzon_calc()
async def calc_fstring_value_only_matrix():
    """Render a matrix in the f-string value-only path."""
    matrix = [[1, 2], [3, 4]]
    f"matrix: {matrix}"


@uzon_calc()
async def calc_tensor_substitution_sheet():
    """Render tensor construction and indexed access substitution."""
    import numpy as np

    a5 = np.array([[1, 2, 3], [4, 5, 6]])
    index1 = 0
    index2 = 1
    value = a5[index1, index2]


def _render_value_root(value):
    """Render a runtime value to a parsed MathML root."""
    return ET.fromstring(value_to_ir(value).to_mathml_xml())


def _render_expression_root(expression: str):
    """Render a Python expression to a parsed MathML root."""
    expression_node = ast.parse(expression, mode="eval").body
    return ET.fromstring(expr_to_ir(expression_node).to_mathml_xml())


def _find_matrix(root):
    """Find the first matrix table in a parsed MathML root."""
    return root.find(".//m:mtable", MATHML_NAMESPACE)


def _plain_text(content: str) -> str:
    """Convert HTML/MathML content to compact readable text."""
    return html.unescape(re.sub(r"<[^>]+>", "", content)).replace(" ", "")


def _read_effective_math_style():
    """Read math styles after removing CSS comments."""
    style_content = MATH_STYLE_PATH.read_text(encoding="utf-8")
    return CSS_COMMENT_PATTERN.sub("", style_content)


def _extract_css_rule_block(style_content: str, selector: str) -> str:
    """Extract a CSS rule body for a selector."""
    rule_pattern = re.compile(
        rf"{re.escape(selector)}\s*\{{(?P<body>.*?)\}}", re.DOTALL
    )
    rule_match = rule_pattern.search(style_content)
    assert rule_match is not None
    return rule_match.group("body")


def _assert_css_rule_preserves_mathml_display(
    style_content: str, selector: str
) -> None:
    """Assert a MathML selector does not override native display semantics."""
    rule_block = _extract_css_rule_block(style_content, selector)
    assert "display:" not in rule_block


def test_one_dimensional_array_keeps_inline_array_value():
    """一维数组仍使用原有 array-value 行内展示。"""
    root = _render_value_root([1, 2, 3])

    assert _find_matrix(root) is None
    assert root.find(".//m:mrow[@class='array-value']", MATHML_NAMESPACE) is not None


def test_rectangular_two_dimensional_array_renders_matrix_table():
    """二维矩形数组应渲染为 MathML 矩阵表格。"""
    root = _render_value_root([[1 * unit.m, 2], [3, 4]])

    matrix = _find_matrix(root)
    assert matrix is not None
    rows = matrix.findall("m:mtr", MATHML_NAMESPACE)
    assert len(rows) == 2
    assert [len(row.findall("m:mtd", MATHML_NAMESPACE)) for row in rows] == [2, 2]
    assert matrix.find(".//m:mtext[@class='unit']", MATHML_NAMESPACE).text == "m"


def test_numpy_two_dimensional_array_renders_matrix_table():
    """numpy 二维数组应复用运行期矩阵展示规则。"""
    root = _render_value_root(np.array([[1, 2], [3, 4]]))

    matrix = _find_matrix(root)
    assert matrix is not None
    assert len(matrix.findall("m:mtr", MATHML_NAMESPACE)) == 2


def test_array_like_numeric_scalar_renders_number_node():
    """带 tolist 协议的数值标量应按普通数字渲染。"""
    root = _render_value_root(np.array([[1, 2], [3, 4]])[0, 1])

    assert root.find(".//m:mn", MATHML_NAMESPACE).text == "2"
    assert root.find(".//m:mtext", MATHML_NAMESPACE) is None


def test_three_dimensional_array_renders_outer_array_with_matrix_slices():
    """三维数组保留外层数组结构，并将二维切片显示为矩阵。"""
    root = _render_value_root([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])

    assert len(root.findall(".//m:mtable", MATHML_NAMESPACE)) == 2
    assert root.find(".//m:mrow[@class='array-value']", MATHML_NAMESPACE) is not None


def test_ragged_two_dimensional_array_keeps_nested_array_values():
    """不规则二维数组不应伪装成矩阵。"""
    root = _render_value_root([[1, 2], [3]])

    assert _find_matrix(root) is None
    assert len(root.findall(".//m:mrow[@class='array-value']", MATHML_NAMESPACE)) == 3


def test_ast_rectangular_array_literal_renders_matrix_table():
    """表达式字面量数组与运行期数组保持同样的矩阵展示。"""
    root = _render_expression_root("[[1, 2], [3, 4]]")

    matrix = _find_matrix(root)
    assert matrix is not None
    assert len(matrix.findall("m:mtr", MATHML_NAMESPACE)) == 2


def test_fstring_value_only_array_renders_matrix_fragment():
    """f-string 仅显示值时也应输出矩阵 MathML，而不是 Python repr。"""
    ctx = run_sync(calc_fstring_value_only_matrix)
    content = ctx.contents[-1]

    assert "<mtable" in content
    assert "matrix: " in content
    assert "MTable(rows=" not in content


def test_tensor_constructor_does_not_substitute_module_repr():
    """数组构造调用目标不应在代入式中替换为复杂对象 repr。"""
    ctx = run_sync(calc_tensor_substitution_sheet)
    content = "".join(ctx.contents)
    tensor_line = next(item for item in ctx.contents if ">a5<" in item and ">np<" in item)
    text = _plain_text(tensor_line)

    assert "module'numpy'" not in _plain_text(content)
    assert "a5=np.array" in text
    assert tensor_line.count("<mo>=</mo>") == 2
    assert tensor_line.count("<mtable") == 2


def test_tensor_index_substitution_keeps_index_replacement_before_value():
    """数组下标应先替换索引变量，再显示最终取值。"""
    ctx = run_sync(calc_tensor_substitution_sheet)
    value_line = next(item for item in ctx.contents if ">value<" in item)
    text = _plain_text(value_line)

    assert "value=a5index1,index2=a50,1=2" in text
    assert value_line.count("<mo>=</mo>") == 3
    assert value_line.index(">index1<") < value_line.index(">0<")
    assert value_line.index(">index2<") < value_line.index(">1<")
    assert value_line.rindex(">2<") > value_line.index(">0<")


def test_math_css_preserves_native_matrix_mathml_layout():
    """模板样式不应覆盖矩阵 MathML 的原生布局语义。"""
    style_content = _read_effective_math_style()

    assert "math .array-value" in style_content
    assert "math .array-matrix" in style_content
    assert "math .array-matrix-cell" in style_content
    _assert_css_rule_preserves_mathml_display(style_content, "math .array-value")
    _assert_css_rule_preserves_mathml_display(style_content, "math .array-matrix")
    _assert_css_rule_preserves_mathml_display(style_content, "math .array-matrix-cell")
    assert "padding: var(--uz-space-xs)" in _extract_css_rule_block(
        style_content, "math .array-matrix-cell"
    )
    assert "math > mrow:not(.array-value)" in style_content
    assert "display: inline-flex" in _extract_css_rule_block(
        style_content, "math > mrow:not(.array-value)"
    )
