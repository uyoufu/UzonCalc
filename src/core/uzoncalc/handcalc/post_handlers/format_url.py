from __future__ import annotations

from lxml import etree

from .base_post_handler import BasePostHandler
from .dom_utils import (
    HtmlPart,
    is_tail_in_tag_context,
    is_text_in_tag_context,
    replace_node_tail_with_parts,
    replace_node_text_with_parts,
)

import re


class FormatUrl(BasePostHandler):
    """后处理器：将文本中的网址转换为 a 标签。"""

    priority = 60

    _SKIP_TEXT_TAGS = {"a", "script", "style"}
    _URL_PATTERN = re.compile(
        r"(?<![\w/])"
        r"((?:https?://|www\.)[^\t\n\r\f\v <>'\"\]]+)"
        r"(?=[\s<>'\"\],.;:!?)]|$)",
        re.IGNORECASE,
    )
    _TRAILING_PUNCTUATION = ",.;:!?)]}"

    def handle(self, node: etree._Element, ctx=None) -> None:
        """将当前节点可见文本中的 URL 转换为链接。"""
        if node.text and not is_text_in_tag_context(node, self._SKIP_TEXT_TAGS):
            replace_node_text_with_parts(node, self._format_url_text_parts(node.text))
        if node.tail and not is_tail_in_tag_context(node, self._SKIP_TEXT_TAGS):
            replace_node_tail_with_parts(node, self._format_url_text_parts(node.tail))

    def _format_url_text_parts(self, text: str) -> list[HtmlPart]:
        """将单个文本片段中的 URL 转换为 a 标签片段。"""
        if "http://" not in text and "https://" not in text and "www." not in text:
            return [text]

        pieces: list[HtmlPart] = []
        last_end = 0
        for match in self._URL_PATTERN.finditer(text):
            start, end = match.span(1)
            url_text = match.group(1)

            trailing = ""
            while url_text and url_text[-1] in self._TRAILING_PUNCTUATION:
                trailing = url_text[-1] + trailing
                url_text = url_text[:-1]
                end -= 1

            if not url_text:
                continue

            pieces.append(text[last_end:start])
            pieces.append(self._create_anchor(url_text))
            pieces.append(trailing)
            last_end = end

        if last_end == 0:
            return [text]

        pieces.append(text[last_end:])
        return pieces

    def _create_anchor(self, url_text: str) -> etree._Element:
        """Create an external-link anchor element for URL text."""
        href = (
            url_text
            if url_text.startswith(("http://", "https://"))
            else f"https://{url_text}"
        )
        anchor = etree.Element("a")
        anchor.set("href", href)
        anchor.set("target", "_blank")
        anchor.set("rel", "noopener noreferrer")
        anchor.text = url_text
        return anchor
