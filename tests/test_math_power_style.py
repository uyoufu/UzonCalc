import ast
from pathlib import Path
import xml.etree.ElementTree as ET

from core.uzoncalc.handcalc.ast_to_ir import expr_to_ir


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MATH_STYLE_PATH = PROJECT_ROOT / "src/core/uzoncalc/template/js/src/styles/math.css"
LEGACY_TEMPLATE_STYLE_PATH = PROJECT_ROOT / "tests/template.css"
MATHML_NAMESPACE = {"m": "http://www.w3.org/1998/Math/MathML"}


def _read_style_content(style_path: Path) -> str:
    """读取样式文件内容，便于复用幂标样式断言。"""
    # 样式断言只关注静态 CSS，避免依赖浏览器渲染环境。
    return style_path.read_text(encoding="utf-8")


def _assert_power_exponent_style(style_content: str) -> None:
    """断言幂标样式包含缩小字号规则。"""
    # CSS 只负责缩小幂标，实际间距由 MathML mspace 保证。
    assert "msup > :nth-child(2)" in style_content
    assert "font-size: 0.75em" in style_content
    assert "line-height: 1" in style_content
    assert "margin-left" not in _extract_power_exponent_style_block(style_content)


def _extract_power_exponent_style_block(style_content: str) -> str:
    """提取幂标样式块，避免断言误伤其它 MathML 规则。"""
    # 静态样式简单稳定，按选择器和右花括号截取即可。
    block_start = style_content.index("msup > :nth-child(2)")
    block_end = style_content.index("}", block_start)
    return style_content[block_start:block_end]


def _render_expression_mathml(expression: str) -> str:
    """将表达式渲染为 MathML，便于检查幂标结构。"""
    # 只解析表达式主体，避免依赖完整计算上下文。
    expression_node = ast.parse(expression, mode="eval").body
    return expr_to_ir(expression_node).to_mathml_xml()


def test_template_math_power_exponent_style_is_compact():
    """模板数学样式应让幂数字更小且不紧贴变量。"""
    style_content = _read_style_content(MATH_STYLE_PATH)

    _assert_power_exponent_style(style_content)


def test_power_exponent_uses_mathml_space_before_number():
    """幂标数字前应插入 MathML 间距，避免贴近变量底数。"""
    mathml = _render_expression_mathml("H**2")
    root = ET.fromstring(mathml)

    exponent_row = root.find(".//m:msup/m:mrow[2]", MATHML_NAMESPACE)
    assert exponent_row is not None
    assert exponent_row.find("m:mspace", MATHML_NAMESPACE).attrib["width"] == "0.2em"
    assert exponent_row.find("m:mn", MATHML_NAMESPACE).text == "2"


def test_parenthesized_power_exponent_does_not_add_extra_space():
    """括号底数已有视觉边界，幂标前不应再插入额外间距。"""
    mathml = _render_expression_mathml("(H + L) ** 2")
    root = ET.fromstring(mathml)

    exponent_row = root.find(".//m:msup/m:mrow[2]", MATHML_NAMESPACE)
    assert exponent_row is not None
    assert exponent_row.find("m:mspace", MATHML_NAMESPACE) is None
    assert exponent_row.find("m:mn", MATHML_NAMESPACE).text == "2"


def test_legacy_template_math_power_exponent_style_keeps_parity():
    """旧模板样式样本应与实际模板保持幂标规则一致。"""
    style_content = _read_style_content(LEGACY_TEMPLATE_STYLE_PATH)

    _assert_power_exponent_style(style_content)
