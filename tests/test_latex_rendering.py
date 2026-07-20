from uzoncalc.context import CalcContext
from uzoncalc.context_options import ContextOptions
from uzoncalc.context_utils.elements import LaTex, laTex
from uzoncalc.globals import _calc_instance
from uzoncalc.template.utils import render_html_template


def test_latex_element_renders_dedicated_tag_with_escaped_content():
    """laTex 应输出专用标签，并保留原始公式文本。"""
    html = laTex(r"x_i^2 < y & \frac{a_b}{c^d}")

    assert html == (
        r'<latex class="latex">x_i^2 &lt; y &amp; \frac{a_b}{c^d}</latex>'
    )


def test_latex_function_persists_content_without_script_notation_conversion():
    """LaTex 写入上下文时不应被脚本标记后处理器改写。"""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        LaTex(r"x_i^2 + \frac{a_b}{c^d}")
    finally:
        _calc_instance.reset(token)

    assert context.contents[-1] == (
        r'<latex class="latex">x_i^2 + \frac{a_b}{c^d}</latex>'
    )


def test_latex_function_persists_backslash_commands_for_katex():
    """LaTex 写入上下文后应保留 KaTeX 需要的反斜杠命令。"""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        LaTex(r"\gamma_0 M_d \le M_{ud}")
    finally:
        _calc_instance.reset(token)

    assert context.contents[-1] == (
        r'<latex class="latex">\gamma_0 M_d \le M_{ud}</latex>'
    )


def test_rendered_template_loads_katex_runtime():
    """HTML 模板应加载 KaTeX，渲染逻辑由模板 JS 接管。"""
    html = render_html_template("<latex>x_i^2</latex>", ContextOptions())

    assert "katex.min.css" in html
    assert "katex.min.js" in html
    assert "document.querySelectorAll('latex.latex')" not in html
    assert "displayMode: true" not in html
