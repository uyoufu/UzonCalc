from core.uzoncalc.handcalc.post_handlers.comparison_symbol import ComparisonSymbol
from core.uzoncalc.handcalc.post_handlers.post_pipeline import get_default_post_handlers


def test_comparison_symbol_converts_plain_text_operators():
    """普通文本中的比较运算符应转换为数学比较符号。"""
    handler = ComparisonSymbol()

    assert handler.handle("a <= b, c >= d, e != f, g == h") == (
        "a ≤ b, c ≥ d, e ≠ f, g ≡ h"
    )


def test_comparison_symbol_converts_html_text_nodes_only():
    """HTML 文本节点中的比较运算符应转换，标签属性应保持原样。"""
    handler = ComparisonSymbol()

    html = '<p data-rule="a <= b">a <= b and c >= d</p>'

    assert handler.handle(html) == '<p data-rule="a <= b">a ≤ b and c ≥ d</p>'


def test_comparison_symbol_converts_escaped_angle_operators():
    """Markdown 等已转义文本中的比较运算符应转换为数学符号。"""
    handler = ComparisonSymbol()

    html = "<p>a &lt;= b and c &gt;= d</p>"

    assert handler.handle(html) == "<p>a ≤ b and c ≥ d</p>"


def test_comparison_symbol_skips_code_pre_and_latex_text():
    """代码类和 LaTeX 标签中的比较运算符应保持原样。"""
    handler = ComparisonSymbol()

    html = (
        "<p>a <= b</p>"
        "<code>c <= d</code>"
        "<pre>e >= f</pre>"
        "<latex>g <= h</latex>"
    )

    assert handler.handle(html) == (
        "<p>a ≤ b</p>"
        "<code>c <= d</code>"
        "<pre>e >= f</pre>"
        "<latex>g <= h</latex>"
    )


def test_comparison_symbol_is_registered_in_default_pipeline():
    """默认后处理管道应启用比较符号转换处理器。"""
    handler_names = [
        handler.__class__.__name__ for handler in get_default_post_handlers()
    ]

    assert "ComparisonSymbol" in handler_names
