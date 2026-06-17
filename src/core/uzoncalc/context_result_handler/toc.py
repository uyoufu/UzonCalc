from __future__ import annotations

from dataclasses import dataclass
import html
from html.parser import HTMLParser

from .base_context_result_handler import BaseContextResultHandler
from ..service.toc_page_numbers import render_heading_marker

_HEADING_TAGS = {"h2", "h3", "h4", "h5", "h6"}
_MIN_HEADING_LEVEL = 2
_MAX_COUNTER_COUNT = 5
_TOC_INJECTION_MARK = "\x00UZONCALC_TOC_INJECTION\x00"


@dataclass
class _ElementState:
    tag: str
    is_inside_toc: bool
    is_toc_container: bool


@dataclass
class _HeadingItem:
    heading_id: str
    text: str
    indent_level: int
    section_number: str


@dataclass
class _OpenHeading:
    tag: str
    heading_id: str
    text_parts: list[str]


class _TocHtmlParser(HTMLParser):
    """单次流式扫描正文 HTML，补标题 id 并记录目录注入点。"""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.output_parts: list[str] = []
        self.headings: list[_HeadingItem] = []
        self.element_stack: list[_ElementState] = []
        self.open_headings: list[_OpenHeading] = []
        self.heading_counters = [0 for _ in range(_MAX_COUNTER_COUNT)]
        self.heading_index = 0
        self.toc_container_depth: int | None = None
        self.toc_container_has_content = False
        self.has_toc_injection_mark = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        normalized_tag = tag.lower()
        attr_values = dict(attrs)
        element_id = attr_values.get("id")
        is_inside_toc = self._is_inside_toc() or element_id == "toc"
        is_toc_container = is_inside_toc and element_id == "toc-container"

        if is_toc_container and self.toc_container_depth is None:
            self.toc_container_depth = len(self.element_stack)
            self.toc_container_has_content = False
        elif self.toc_container_depth is not None:
            self._mark_toc_container_content()

        start_tag = self.get_starttag_text() or self._render_start_tag(tag, attrs)
        if (
            normalized_tag in _HEADING_TAGS
            and not is_inside_toc
            and not self._heading_has_id(attrs)
        ):
            heading_id = f"heading-{self.heading_index}"
            start_tag = self._inject_id(start_tag, heading_id)
        else:
            heading_id = element_id or f"heading-{self.heading_index}"

        self.output_parts.append(start_tag)
        self.element_stack.append(
            _ElementState(
                tag=normalized_tag,
                is_inside_toc=is_inside_toc,
                is_toc_container=is_toc_container,
            )
        )

        if normalized_tag in _HEADING_TAGS and not is_inside_toc:
            self.output_parts.append(render_heading_marker(heading_id))
            self.open_headings.append(
                _OpenHeading(
                    tag=normalized_tag,
                    heading_id=heading_id,
                    text_parts=[],
                )
            )
            self.heading_index += 1

    def handle_endtag(self, tag: str):
        normalized_tag = tag.lower()

        if (
            self.toc_container_depth is not None
            and len(self.element_stack) - 1 == self.toc_container_depth
            and self.element_stack[-1].is_toc_container
            and not self.toc_container_has_content
        ):
            self.output_parts.append(_TOC_INJECTION_MARK)
            self.has_toc_injection_mark = True

        if normalized_tag in _HEADING_TAGS and self.open_headings:
            open_heading = self.open_headings[-1]
            if open_heading.tag == normalized_tag:
                self.open_headings.pop()
                self._append_heading_item(open_heading)

        self.output_parts.append(f"</{tag}>")
        if self.element_stack:
            closed_state = self.element_stack.pop()
            if closed_state.is_toc_container:
                self.toc_container_depth = None

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]):
        self.output_parts.append(
            self.get_starttag_text() or self._render_start_tag(tag, attrs, True)
        )
        self._mark_toc_container_content()

    def handle_data(self, data: str):
        self.output_parts.append(data)
        self._append_heading_text(data)
        if data.strip():
            self._mark_toc_container_content()

    def handle_entityref(self, name: str):
        text = f"&{name};"
        self.output_parts.append(text)
        self._append_heading_text(html.unescape(text))
        self._mark_toc_container_content()

    def handle_charref(self, name: str):
        text = f"&#{name};"
        self.output_parts.append(text)
        self._append_heading_text(html.unescape(text))
        self._mark_toc_container_content()

    def handle_comment(self, data: str):
        self.output_parts.append(f"<!--{data}-->")

    def handle_decl(self, decl: str):
        self.output_parts.append(f"<!{decl}>")

    def handle_pi(self, data: str):
        self.output_parts.append(f"<?{data}>")

    def unknown_decl(self, data: str):
        self.output_parts.append(f"<![{data}]>")

    def close(self):
        super().close()
        if self.open_headings:
            for open_heading in self.open_headings:
                self._append_heading_item(open_heading)
            self.open_headings.clear()

    def render(self) -> str:
        toc_html = self._render_toc_html()
        return "".join(
            toc_html if part == _TOC_INJECTION_MARK else part
            for part in self.output_parts
        )

    def _append_heading_item(self, open_heading: _OpenHeading):
        """根据标题层级更新章节编号并记录目录项。"""
        indent_level = int(open_heading.tag[1:]) - _MIN_HEADING_LEVEL
        if indent_level < 0 or indent_level >= _MAX_COUNTER_COUNT:
            return

        self.heading_counters[indent_level] += 1
        for index in range(indent_level + 1, len(self.heading_counters)):
            self.heading_counters[index] = 0

        section_values = [
            str(value)
            for value in self.heading_counters[: indent_level + 1]
            if value > 0
        ]
        self.headings.append(
            _HeadingItem(
                heading_id=open_heading.heading_id,
                text="".join(open_heading.text_parts).strip(),
                indent_level=indent_level,
                section_number=".".join(section_values),
            )
        )

    def _append_heading_text(self, text: str):
        """收集当前标题的纯文本内容。"""
        if self.open_headings:
            self.open_headings[-1].text_parts.append(text)

    def _is_inside_toc(self) -> bool:
        return bool(self.element_stack and self.element_stack[-1].is_inside_toc)

    def _mark_toc_container_content(self):
        if self.toc_container_depth is not None:
            self.toc_container_has_content = True

    def _heading_has_id(self, attrs: list[tuple[str, str | None]]) -> bool:
        return any(attr_name.lower() == "id" for attr_name, _ in attrs)

    def _inject_id(self, start_tag: str, heading_id: str) -> str:
        """向标题开始标签补充稳定 id 属性。"""
        if start_tag.endswith(">"):
            return f'{start_tag[:-1]} id="{html.escape(heading_id, quote=True)}">'
        return start_tag

    def _render_start_tag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
        is_self_closing: bool = False,
    ) -> str:
        attr_parts = []
        for attr_name, attr_value in attrs:
            if attr_value is None:
                attr_parts.append(attr_name)
                continue
            attr_parts.append(f'{attr_name}="{html.escape(attr_value, quote=True)}"')
        attrs_text = f" {' '.join(attr_parts)}" if attr_parts else ""
        suffix = " /" if is_self_closing else ""
        return f"<{tag}{attrs_text}{suffix}>"

    def _render_toc_html(self) -> str:
        if not self.has_toc_injection_mark:
            return ""

        toc_parts = ['<div class="toc-list">']
        for heading in self.headings:
            toc_parts.append(
                "\n"
                f'    <div class="toc-item" style="margin-left: {heading.indent_level}rem;">\n'
                f'      <a href="#{html.escape(heading.heading_id, quote=True)}" class="toc-link">\n'
                f'        <span class="toc-number">{html.escape(heading.section_number)}</span>\n'
                f'        <span class="toc-text">{html.escape(heading.text)}</span>\n'
                '        <span class="toc-dots"></span>\n'
                f'        <span class="toc-page" data-heading-id="{html.escape(heading.heading_id, quote=True)}" data-page-placeholder="true">&nbsp;</span>\n'
                "      </a>\n"
                "    </div>"
            )
        toc_parts.append("</div>")
        return "".join(toc_parts)


class TocContextResultHandler(BaseContextResultHandler):
    """当文档包含 toc 占位符时生成目录内容。"""

    priority = 50

    def handle(self, html: str, ctx=None) -> str:
        if "toc-container" not in html:
            return html

        parser = _TocHtmlParser()
        parser.feed(html)
        parser.close()
        if not parser.has_toc_injection_mark:
            return html
        return parser.render()
