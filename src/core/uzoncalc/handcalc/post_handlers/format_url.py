from __future__ import annotations

import html
import re

from .base_post_handler import BasePostHandler


class FormatUrl(BasePostHandler):
    """后处理器：将文本中的网址转换为 a 标签。"""

    priority = 60

    _ANCHOR_PATTERN = re.compile(r"<a\b[^>]*>.*?</a>", re.IGNORECASE | re.DOTALL)
    _RAW_TEXT_TAG_PATTERN = re.compile(
        r"<(script|style)\b[^>]*>.*?</\1>",
        re.IGNORECASE | re.DOTALL,
    )
    _TAG_PATTERN = re.compile(r"<[^>]+>")
    _URL_PATTERN = re.compile(
        r"(?<![\w/])"
        r"((?:https?://|www\.)[^	\n\r\f\v <>'\"\]]+)"
        r"(?=[\s<>'\"\],.;:!?)]|$)",
        re.IGNORECASE,
    )
    _TRAILING_PUNCTUATION = ",.;:!?)]}"

    def handle(self, data: str, ctx=None) -> str:
        if "http://" not in data and "https://" not in data and "www." not in data:
            return data

        anchors: list[str] = []

        def _save_anchor(match: re.Match[str]) -> str:
            anchors.append(match.group(0))
            return f"\x00ANCHOR_{len(anchors) - 1}\x00"

        data = self._ANCHOR_PATTERN.sub(_save_anchor, data)

        ignored_ranges = self._get_ignored_ranges(data)
        data = self._format_html_text_urls(data, ignored_ranges)

        def _restore_anchor(match: re.Match[str]) -> str:
            return anchors[int(match.group(1))]

        return re.sub(r"\x00ANCHOR_(\d+)\x00", _restore_anchor, data)

    def _get_ignored_ranges(self, data: str) -> list[tuple[int, int]]:
        """获取需要原样保留的 script/style 区间。"""
        # JS/CSS 是原始文本，不能执行 URL 链接化或 HTML 转义。
        return [match.span(0) for match in self._RAW_TEXT_TAG_PATTERN.finditer(data)]

    def _format_html_text_urls(
        self, data: str, ignored_ranges: list[tuple[int, int]]
    ) -> str:
        """仅在忽略区间之外执行 URL 链接化。"""
        if not ignored_ranges:
            return self._process_html_chunk_urls(data)

        pieces: list[str] = []
        last_end = 0
        for start, end in ignored_ranges:
            pieces.append(self._process_html_chunk_urls(data[last_end:start]))
            pieces.append(data[start:end])
            last_end = end

        pieces.append(self._process_html_chunk_urls(data[last_end:]))
        return "".join(pieces)

    def _process_html_chunk_urls(self, chunk: str) -> str:
        """处理普通 HTML 片段中的文本节点 URL。"""
        parts = self._TAG_PATTERN.split(chunk)
        tags = self._TAG_PATTERN.findall(chunk)
        if not tags:
            return self._replace_text_segment_urls(chunk)

        rebuilt: list[str] = []
        for index, part in enumerate(parts):
            rebuilt.append(self._replace_text_segment_urls(part))
            if index < len(tags):
                rebuilt.append(tags[index])
        return "".join(rebuilt)

    def _replace_text_segment_urls(self, segment: str) -> str:
        """将单个文本片段中的 URL 转换为 a 标签。"""
        if not segment:
            return segment

        decoded = html.unescape(segment)
        if (
            "http://" not in decoded
            and "https://" not in decoded
            and "www." not in decoded
        ):
            return segment

        pieces: list[str] = []
        last_end = 0
        for match in self._URL_PATTERN.finditer(decoded):
            start, end = match.span(1)
            url_text = match.group(1)

            trailing = ""
            while url_text and url_text[-1] in self._TRAILING_PUNCTUATION:
                trailing = url_text[-1] + trailing
                url_text = url_text[:-1]
                end -= 1

            if not url_text:
                continue

            pieces.append(html.escape(decoded[last_end:start]))
            href = (
                url_text
                if url_text.startswith(("http://", "https://"))
                else f"https://{url_text}"
            )
            pieces.append(
                f'<a href="{html.escape(href, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(url_text)}</a>'
            )
            pieces.append(html.escape(trailing))
            last_end = end

        if last_end == 0:
            return segment

        pieces.append(html.escape(decoded[last_end:]))
        return "".join(pieces)
