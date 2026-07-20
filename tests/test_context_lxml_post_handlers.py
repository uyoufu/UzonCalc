from uzoncalc.context import CalcContext
from uzoncalc.handcalc.post_handlers.comparison_symbol import ComparisonSymbol
from uzoncalc.handcalc.post_handlers.script_notation import ScriptNotation
from uzoncalc.handcalc.post_handlers.swap_symbol import SwapSymbol


def test_context_post_handlers_convert_plain_text_content():
    """纯文本 content 应通过 lxml 后处理管道正常转换。"""
    ctx = CalcContext()
    ctx.options.post_handlers = [ComparisonSymbol(), SwapSymbol(), ScriptNotation()]

    ctx.append_content(r"alpha <= beta and E_j")

    assert ctx.html_content() == r"α ≤ β and E<sub>j</sub>"


def test_context_post_handlers_convert_html_fragment_content():
    """HTML 片段 content 应只转换可见文本，不修改属性。"""
    ctx = CalcContext()
    ctx.options.post_handlers = [ComparisonSymbol(), ScriptNotation()]

    ctx.append_content('<p data-name="E_j">E_j <= E_k</p>')

    assert ctx.html_content() == (
        '<p data-name="E_j">E<sub>j</sub> ≤ E<sub>k</sub></p>'
    )


def test_context_post_handlers_chain_alias_into_script_notation():
    """别名替换后的文本应继续交给后续上下标处理器。"""
    ctx = CalcContext()
    ctx.options.aliases["stress"] = "E_j"

    ctx.append_content("stress")

    assert ctx.html_content() == "E<sub>j</sub>"
