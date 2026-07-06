from core.uzoncalc.handcalc.post_handlers.dom_utils import (
    FRAGMENT_ROOT_TAG,
    parse_html_fragment,
    serialize_html_fragment,
)


def test_parse_html_fragment_uses_fixed_temporary_root():
    """HTML 片段应包在固定临时根中，序列化结果不包含临时根。"""
    root = parse_html_fragment("<p>x</p><p>y</p>")

    assert root.tag == FRAGMENT_ROOT_TAG
    assert serialize_html_fragment(root) == "<p>x</p><p>y</p>"


def test_serialize_html_fragment_uses_lxml_native_html_output():
    """原生 HTML 序列化不再强制转义普通文本引号。"""
    assert serialize_html_fragment(parse_html_fragment("'a' \"b\"")) == "'a' \"b\""
    assert (
        serialize_html_fragment(parse_html_fragment("<option selected>One</option>"))
        == "<option selected>One</option>"
    )
