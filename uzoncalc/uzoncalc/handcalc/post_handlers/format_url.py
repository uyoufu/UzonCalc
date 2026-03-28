from __future__ import annotations

import html
import re

from .base_post_handler import BasePostHandler


class FormatUrl(BasePostHandler):
    """后处理器：将文本中的网址转换为 a 标签。"""

    priority = 60

    _ANCHOR_PATTERN = re.compile(r"<a\b[^>]*>.*?</a>", re.IGNORECASE | re.DOTALL)
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

        def _replace_text_segment(segment: str) -> str:
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

        def _process_chunk(chunk: str) -> str:
            parts = self._TAG_PATTERN.split(chunk)
            tags = self._TAG_PATTERN.findall(chunk)
            if not tags:
                return _replace_text_segment(chunk)

            rebuilt: list[str] = []
            for index, part in enumerate(parts):
                rebuilt.append(_replace_text_segment(part))
                if index < len(tags):
                    rebuilt.append(tags[index])
            return "".join(rebuilt)

        data = re.sub(
            r"(?:[^<]+|<[^>]+>)+",
            lambda match: _process_chunk(match.group(0)),
            data,
        )

        def _restore_anchor(match: re.Match[str]) -> str:
            return anchors[int(match.group(1))]

        return re.sub(r"\x00ANCHOR_(\d+)\x00", _restore_anchor, data)
