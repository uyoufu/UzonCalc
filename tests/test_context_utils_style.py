"""Tests for inline style helpers in context_utils.style."""

from uzoncalc.context import CalcContext
from uzoncalc.context_utils import Bold, Italic, bold, italic
from uzoncalc.globals import _calc_instance


def test_lowercase_style_helpers_return_html_string():
    """Lowercase style helpers should return HTML without persisting content."""
    assert bold("重要") == "<b>重要</b>"
    assert italic("说明") == "<i>说明</i>"


def test_style_helpers_keep_nested_html_fragments():
    """Style helpers should preserve existing HTML fragments in children."""
    assert bold(["A", italic("B")]) == "<b>A<i>B</i></b>"


def test_uppercase_style_helpers_persist_html_to_current_context():
    """Uppercase style helpers should append rendered HTML to the active context."""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        Bold("重要")
        Italic("说明")
    finally:
        _calc_instance.reset(token)

    assert context.contents == ["<p><b>重要</b></p>", "<p><i>说明</i></p>"]
