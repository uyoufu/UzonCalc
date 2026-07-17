from uzoncalc.handcalc.post_handlers.format_url import FormatUrl
from uzoncalc.handcalc.post_handlers.dom_utils import (
    PostHandlerNode,
    parse_html_fragment,
    serialize_html_fragment,
)


def render_with_handler(handler, html: str) -> str:
    root = parse_html_fragment(html)
    for node in list(root.iter()):
        handler.handle(PostHandlerNode(node))
    return serialize_html_fragment(root)


def test_format_url_converts_plain_text_url():
    """普通文本中的 URL 应转换为链接。"""
    handler = FormatUrl()

    html = "<p>参考 https://example.com/docs</p>"

    assert render_with_handler(handler, html) == (
        '<p>参考 <a href="https://example.com/docs" target="_blank" '
        'rel="noopener noreferrer">https://example.com/docs</a></p>'
    )


def test_format_url_keeps_existing_anchor():
    """已有 a 标签不应被重复转换。"""
    handler = FormatUrl()

    html = '<p><a href="https://example.com">https://example.com</a></p>'

    assert render_with_handler(handler, html) == html


def test_format_url_skips_script_content():
    """script 内的 URL 与 JavaScript 字符串应保持原样。"""
    handler = FormatUrl()

    html = (
        '<script>const option = {"url": "https://example.com/app.js", '
        '"text": "A & B"};</script>'
    )

    assert render_with_handler(handler, html) == html


def test_format_url_skips_style_content():
    """style 内的 URL 与 CSS 字符串应保持原样。"""
    handler = FormatUrl()

    html = '<style>.hero { background: url("https://example.com/bg.png"); }</style>'

    assert render_with_handler(handler, html) == html


def test_format_url_converts_url_outside_raw_text_tags():
    """原始文本标签外部的 URL 仍应自动转换。"""
    handler = FormatUrl()

    html = (
        "<p>文档 https://example.com/docs</p>"
        '<script>const texture = "https://example.com/earth.jpg";</script>'
    )

    assert render_with_handler(handler, html) == (
        '<p>文档 <a href="https://example.com/docs" target="_blank" '
        'rel="noopener noreferrer">https://example.com/docs</a></p>'
        '<script>const texture = "https://example.com/earth.jpg";</script>'
    )


def test_format_url_skips_uppercase_raw_text_tags():
    """大小写不同的原始文本标签也应跳过。"""
    handler = FormatUrl()

    html = '<SCRIPT>const href = "https://example.com/app.js";</SCRIPT>'

    assert render_with_handler(handler, html) == (
        '<script>const href = "https://example.com/app.js";</script>'
    )
