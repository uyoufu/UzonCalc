from core.uzoncalc.context import CalcContext
from core.uzoncalc.handcalc.post_handlers.comparison_symbol import ComparisonSymbol
from core.uzoncalc.handcalc.post_handlers.script_notation import ScriptNotation
from core.uzoncalc.handcalc.post_handlers.swap_symbol import SwapSymbol


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
