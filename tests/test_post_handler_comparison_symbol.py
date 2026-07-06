from core.uzoncalc.handcalc.post_handlers.comparison_symbol import ComparisonSymbol
from core.uzoncalc.handcalc.post_handlers.dom_utils import (
    PostHandlerNode,
    parse_html_fragment,
    serialize_html_fragment,
)
from core.uzoncalc.handcalc.post_handlers.post_pipeline import get_default_post_handlers


def render_with_handler(handler, html: str) -> str:
    root = parse_html_fragment(html)
    for node in list(root.iter()):
        handler.handle(PostHandlerNode(node))
    return serialize_html_fragment(root)


def test_comparison_symbol_converts_plain_text_operators():
    """普通文本中的比较运算符应转换为数学比较符号。"""
    handler = ComparisonSymbol()

    assert render_with_handler(handler, "a <= b, c >= d, e != f, g == h") == (
        "a ≤ b, c ≥ d, e ≠ f, g ≡ h"
    )


def test_comparison_symbol_converts_html_text_nodes_only():
    """HTML 文本节点中的比较运算符应转换，标签属性应保持原样。"""
    handler = ComparisonSymbol()

    html = '<p data-rule="a <= b">a <= b and c >= d</p>'

    assert render_with_handler(handler, html) == '<p data-rule="a &lt;= b">a ≤ b and c ≥ d</p>'


def test_comparison_symbol_converts_escaped_angle_operators():
    """Markdown 等已转义文本中的比较运算符应转换为数学符号。"""
    handler = ComparisonSymbol()

    html = "<p>a &lt;= b and c &gt;= d</p>"

    assert render_with_handler(handler, html) == "<p>a ≤ b and c ≥ d</p>"


def test_comparison_symbol_skips_code_pre_and_latex_text():
    """代码类和 LaTeX 标签中的比较运算符应保持原样。"""
    handler = ComparisonSymbol()

    html = (
        "<p>a <= b</p>"
        "<code>c <= d</code>"
        "<pre>e >= f</pre>"
        "<latex>g <= h</latex>"
    )

    assert render_with_handler(handler, html) == (
        "<p>a ≤ b</p>"
        "<code>c &lt;= d</code>"
        "<pre>e &gt;= f</pre>"
        "<latex>g &lt;= h</latex>"
    )


def test_comparison_symbol_is_registered_in_default_pipeline():
    """默认后处理管道应启用比较符号转换处理器。"""
    handler_names = [
        handler.__class__.__name__ for handler in get_default_post_handlers()
    ]

    assert "ComparisonSymbol" in handler_names
