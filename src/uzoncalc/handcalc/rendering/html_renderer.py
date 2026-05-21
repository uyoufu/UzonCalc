from __future__ import annotations

from ...context import CalcContext

HTML_TAG_SPAN = "span"
HTML_TAG_P = "p"


def render_html(ctx: CalcContext, content: str) -> None:
    """根据 inline 状态写入段落或行内内容。"""
    tag = HTML_TAG_SPAN if ctx.is_inline_mode else HTML_TAG_P
    ctx.append_content(f"<{tag}>{content}</{tag}>")
