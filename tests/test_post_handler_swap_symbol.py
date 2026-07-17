from uzoncalc.handcalc.post_handlers.swap_symbol import SwapSymbol
from uzoncalc.handcalc.post_handlers.dom_utils import (
    PostHandlerNode,
    parse_html_fragment,
    serialize_html_fragment,
)
from uzoncalc.context_utils.markdown import get_markdown


def render_with_handler(handler, html: str) -> str:
    root = parse_html_fragment(html)
    for node in list(root.iter()):
        handler.handle(PostHandlerNode(node))
    return serialize_html_fragment(root)


def test_swap_symbol_converts_greek_word():
    """希腊字母英文名称应转换为对应数学符号。"""
    handler = SwapSymbol()

    assert render_with_handler(handler, "alpha") == "α"


def test_swap_symbol_unescapes_backslash_and_skips_conversion():
    """反斜杠转义的希腊字母英文名称应保持英文名称。"""
    handler = SwapSymbol()

    assert render_with_handler(handler, r"\alpha") == "alpha"


def test_swap_symbol_no_longer_skips_quoted_text():
    """引号不再作为保护边界，引号内英文名称仍应转换。"""
    handler = SwapSymbol()

    assert render_with_handler(handler, "'alpha' \"alpha\"") == "'α' \"α\""


def test_swap_symbol_converts_only_unescaped_greek_word():
    """转义和未转义的希腊字母英文名称混用时应分别处理。"""
    handler = SwapSymbol()

    assert render_with_handler(handler, r"\alpha (alpha)") == "alpha (α)"


def test_swap_symbol_does_not_convert_word_after_unconsumed_backslash():
    """无法作为独立转义标记消费的反斜杠后名称不应被二次匹配。"""
    handler = SwapSymbol()

    assert render_with_handler(handler, r"x\alpha") == r"x\alpha"


def test_swap_symbol_skips_code_text():
    """代码标签中的希腊字母名称和反斜杠应保持原样。"""
    handler = SwapSymbol()

    html = r"<p><code>\alpha</code> alpha \alpha</p>"

    assert render_with_handler(handler, html) == r"<p><code>\alpha</code> α alpha</p>"


def test_swap_symbol_skips_latex_text():
    """LaTeX 标签中的反斜杠命令应交给 KaTeX 处理。"""
    handler = SwapSymbol()

    html = r'<p>gamma \gamma</p><latex class="latex">\gamma_0</latex>'

    assert render_with_handler(handler, html) == (
        r'<p>γ gamma</p><latex class="latex">\gamma_0</latex>'
    )


def test_swap_symbol_keeps_markdown_code_span_backslash():
    """Markdown 行内代码中的反斜杠不应被转义规则移除。"""
    handler = SwapSymbol()
    html = get_markdown().render("`\\alpha`")

    assert render_with_handler(handler, html).strip() == r"<p><code>\alpha</code></p>"
