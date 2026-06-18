from core.uzoncalc.handcalc.post_handlers.subscripting import Subscripting


def test_subscripting_converts_plain_html_text_nodes():
    """普通 HTML 文本节点中的变量下标应自动转换。"""
    handler = Subscripting()

    html = "<p>规范式 (4.2.3-1) 至 (4.2.3-3) 用于计算 E_j 和 e_j。</p>"

    assert handler.handle(html) == (
        "<p>规范式 (4.2.3-1) 至 (4.2.3-3) 用于计算 "
        "E<sub>j</sub> 和 e<sub>j</sub>。</p>"
    )


def test_subscripting_keeps_html_attributes_unchanged():
    """HTML 属性中的下划线文本不应被误转换。"""
    handler = Subscripting()

    html = '<td class="E_j" data-name="e_j">单位宽度静土压力 E_j</td>'

    assert handler.handle(html) == (
        '<td class="E_j" data-name="e_j">单位宽度静土压力 E<sub>j</sub></td>'
    )


def test_subscripting_skips_code_and_pre_text():
    """代码类标签中的内容应保持原样。"""
    handler = Subscripting()

    html = "<p>E_j</p><code>E_j</code><pre>e_j</pre>"

    assert handler.handle(html) == (
        "<p>E<sub>j</sub></p><code>E_j</code><pre>e_j</pre>"
    )


def test_subscripting_skips_url_text():
    """URL 文本中的下划线变量片段不应被转换。"""
    handler = Subscripting()

    html = "<p>参考 https://example.com/docs/E_j?name=e_j 和变量 E_j</p>"

    assert handler.handle(html) == (
        "<p>参考 https://example.com/docs/E_j?name=e_j 和变量 E<sub>j</sub></p>"
    )


def test_subscripting_keeps_mathml_mi_behavior():
    """MathML mi 标签仍使用原有 msub 结构。"""
    handler = Subscripting()

    html = "<math><mi>E_j</mi></math>"

    assert handler.handle(html) == "<math><msub><mi>E</mi><mtext>j</mtext></msub></math>"


def test_subscripting_unescapes_plain_text_and_skips_conversion():
    """普通文本中反斜杠转义的下划线变量应保持原变量名。"""
    handler = Subscripting()

    html = r"<p>\f_y 和 f_y</p>"

    assert handler.handle(html) == "<p>f_y 和 f<sub>y</sub></p>"


def test_subscripting_unescapes_mathml_mi_and_skips_conversion():
    """MathML mi 中反斜杠转义的下划线变量不应生成 msub。"""
    handler = Subscripting()

    html = r"<math><mi>\f_y</mi></math>"

    assert handler.handle(html) == "<math><mi>f_y</mi></math>"


def test_subscripting_does_not_convert_name_after_unconsumed_backslash():
    """无法作为独立转义标记消费的反斜杠后变量不应被二次匹配。"""
    handler = Subscripting()

    html = r"<p>x\f_y 和 f_y</p>"

    assert handler.handle(html) == r"<p>x\f_y 和 f<sub>y</sub></p>"
