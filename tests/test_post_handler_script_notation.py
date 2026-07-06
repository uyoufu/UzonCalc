from core.uzoncalc.handcalc.post_handlers.script_notation import ScriptNotation
from core.uzoncalc.handcalc.post_handlers.dom_utils import (
    parse_html_fragment,
    serialize_html_fragment,
)


def render_with_handler(handler, html: str) -> str:
    root = parse_html_fragment(html)
    for node in list(root.iter()):
        handler.handle(node)
    return serialize_html_fragment(root)


def test_script_notation_converts_plain_html_text_nodes():
    """普通 HTML 文本节点中的变量下标应自动转换。"""
    handler = ScriptNotation()

    html = "<p>规范式 (4.2.3-1) 至 (4.2.3-3) 用于计算 E_j 和 e_j。</p>"

    assert render_with_handler(handler, html) == (
        "<p>规范式 (4.2.3-1) 至 (4.2.3-3) 用于计算 "
        "E<sub>j</sub> 和 e<sub>j</sub>。</p>"
    )


def test_script_notation_keeps_html_attributes_unchanged():
    """HTML 属性中的上下标文本不应被误转换。"""
    handler = ScriptNotation()

    html = '<td class="E_j" data-power="x^2">单位宽度静土压力 E_j 和 x^2</td>'

    assert render_with_handler(handler, html) == (
        '<td class="E_j" data-power="x^2">单位宽度静土压力 '
        "E<sub>j</sub> 和 x<sup>2</sup></td>"
    )


def test_script_notation_skips_code_and_pre_text():
    """代码类标签中的内容应保持原样。"""
    handler = ScriptNotation()

    html = "<p>E_j 和 x^2</p><code>E_j x^2</code><pre>e_j y^3</pre>"

    assert render_with_handler(handler, html) == (
        "<p>E<sub>j</sub> 和 x<sup>2</sup></p>"
        "<code>E_j x^2</code><pre>e_j y^3</pre>"
    )


def test_script_notation_skips_latex_text():
    """LaTeX 标签中的内容应保持原始公式语法。"""
    handler = ScriptNotation()

    html = r'<p>E_j</p><latex class="latex">x_i^2 + \frac{a_b}{c^d}</latex>'

    assert render_with_handler(handler, html) == (
        r"<p>E<sub>j</sub></p>"
        r'<latex class="latex">x_i^2 + \frac{a_b}{c^d}</latex>'
    )


def test_script_notation_skips_url_text():
    """URL 文本中的上下标片段不应被转换。"""
    handler = ScriptNotation()

    html = "<p>参考 https://example.com/docs/E_j?name=x^2 和变量 E_j x^2</p>"

    assert render_with_handler(handler, html) == (
        "<p>参考 https://example.com/docs/E_j?name=x^2 和变量 "
        "E<sub>j</sub> x<sup>2</sup></p>"
    )


def test_script_notation_keeps_mathml_mi_subscript_behavior():
    """MathML mi 标签仍使用原有 msub 结构。"""
    handler = ScriptNotation()

    html = "<math><mi>E_j</mi></math>"

    assert render_with_handler(handler, html) == "<math><msub><mi>E</mi><mtext>j</mtext></msub></math>"


def test_script_notation_converts_mathml_mi_superscript():
    """MathML mi 标签中的上标应转换为 msup。"""
    handler = ScriptNotation()

    html = "<math><mi>x^2</mi></math>"

    assert render_with_handler(handler, html) == "<math><msup><mi>x</mi><mtext>2</mtext></msup></math>"


def test_script_notation_converts_mathml_mi_combined_scripts():
    """MathML mi 标签中的同底上下标应转换为 msubsup。"""
    handler = ScriptNotation()

    html = "<math><mi>x_i^2</mi><mi>y^3_j</mi></math>"

    assert render_with_handler(handler, html) == (
        "<math>"
        "<msubsup><mi>x</mi><mtext>i</mtext><mtext>2</mtext></msubsup>"
        "<msubsup><mi>y</mi><mtext>j</mtext><mtext>3</mtext></msubsup>"
        "</math>"
    )


def test_script_notation_converts_plain_text_superscript_and_groups():
    """普通文本应支持上标和花括号分组。"""
    handler = ScriptNotation()

    html = "<p>x^2, x^{n+1}, x_{i+1}, gamma_混凝土^2</p>"

    assert render_with_handler(handler, html) == (
        "<p>x<sup>2</sup>, x<sup>n+1</sup>, x<sub>i+1</sub>, "
        "gamma<sub>混凝土</sub><sup>2</sup></p>"
    )


def test_script_notation_converts_prime_superscript_with_subscript():
    """单引号应可作为未分组上标并与下标组合。"""
    handler = ScriptNotation()

    html = "<p>a^'_p0</p><math><mi>a^'_p0</mi></math>"

    assert render_with_handler(handler, html) == (
        "<p>a<sub>p0</sub><sup>'</sup></p>"
        "<math><msubsup><mi>a</mi><mtext>p0</mtext>"
        "<mtext>'</mtext></msubsup></math>"
    )


def test_script_notation_combines_scripts_for_same_base_in_any_order():
    """同一底数的上下标应按同底组合输出。"""
    handler = ScriptNotation()

    html = "<p>x_i^2 和 y^3_j</p>"

    assert render_with_handler(handler, html) == (
        "<p>x<sub>i</sub><sup>2</sup> 和 y<sub>j</sub><sup>3</sup></p>"
    )


def test_script_notation_preserves_repeated_subscript_nesting():
    """重复同类下标应延续既有嵌套行为。"""
    handler = ScriptNotation()

    html = "<p>x_1_2</p>"

    assert render_with_handler(handler, html) == "<p>x<sub>1</sub><sub>2</sub></p>"


def test_script_notation_unescapes_plain_text_and_skips_conversion():
    """普通文本中反斜杠转义的上下标变量应保持原变量名。"""
    handler = ScriptNotation()

    html = r"<p>\f_y 和 f_y，\x^2 和 x^2，x\^2</p>"

    assert render_with_handler(handler, html) == (
        "<p>f_y 和 f<sub>y</sub>，x^2 和 x<sup>2</sup>，x^2</p>"
    )


def test_script_notation_unescapes_mathml_mi_and_skips_conversion():
    """MathML mi 中反斜杠转义的上下标变量不应生成脚标结构。"""
    handler = ScriptNotation()

    html = r"<math><mi>\f_y</mi><mi>\x^2</mi></math>"

    assert render_with_handler(handler, html) == "<math><mi>f_y</mi><mi>x^2</mi></math>"


def test_script_notation_does_not_convert_name_after_unconsumed_backslash():
    """无法作为独立转义标记消费的反斜杠后变量不应被二次匹配。"""
    handler = ScriptNotation()

    html = r"<p>x\f_y 和 f_y，q\x^2 和 x^2</p>"

    assert render_with_handler(handler, html) == (
        r"<p>x\f_y 和 f<sub>y</sub>，q\x^2 和 x<sup>2</sup></p>"
    )


def test_script_notation_keeps_invalid_groups_unchanged():
    """空分组、未闭合分组和连续脚标符号应保持原样。"""
    handler = ScriptNotation()

    html = "<p>x_{}, x_{i, x^^2</p>"

    assert render_with_handler(handler, html) == "<p>x_{}, x_{i, x^^2</p>"
