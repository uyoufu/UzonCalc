"""
ToC 页码计算服务。

通过 Playwright 渲染 PDF，并使用 PyMuPDF 从 PDF 文本中定位标题 marker 所在页码。
"""

from __future__ import annotations

import asyncio
import html
import re
import threading
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Coroutine, TypeVar

import fitz

from .playwright_service import get_playwright_service

TOC_PAGE_NUMBERS_ROUTE = "/api/v1/calc/toc-page-numbers"
TOC_HEADING_MARKER_PREFIX = "UZONCALC_TOC_HEADING:"
TOC_HEADING_MARKER_SUFFIX = "|"
_MARKER_PATTERN = re.compile(
    rf"{re.escape(TOC_HEADING_MARKER_PREFIX)}([A-Za-z0-9_.:-]+)"
    rf"{re.escape(TOC_HEADING_MARKER_SUFFIX)}"
)
_T = TypeVar("_T")


def render_heading_marker(heading_id: str) -> str:
    """生成用于 PDF 文本解析的标题 marker。"""
    safe_heading_id = html.escape(heading_id, quote=True)
    marker_text = (
        f"{TOC_HEADING_MARKER_PREFIX}{safe_heading_id}{TOC_HEADING_MARKER_SUFFIX}"
    )
    return (
        '<span class="uz-toc-heading-marker" aria-hidden="true" '
        'style="font-size:0.1px;line-height:0.1px;color:transparent;">'
        f"{marker_text}</span>"
    )


def parse_toc_page_numbers_from_pdf(pdf_bytes: bytes) -> dict[str, int]:
    """从 PDF 字节中解析标题 marker 所在 1-based 页码。"""
    page_numbers: dict[str, int] = {}
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        for page_index, page in enumerate(document):
            text = page.get_text()
            for match in _MARKER_PATTERN.finditer(text):
                heading_id = match.group(1)
                page_numbers.setdefault(heading_id, page_index + 1)
    finally:
        document.close()
    return page_numbers


async def calculate_toc_page_numbers(document_url: str) -> dict[str, int]:
    """按真实打印路径生成 PDF，并返回标题 id 到页码的映射。"""
    pdf_bytes = await get_playwright_service().render_pdf_from_url(document_url)
    return parse_toc_page_numbers_from_pdf(pdf_bytes)


def calculate_toc_page_numbers_sync(document_url: str) -> dict[str, int]:
    """同步计算 ToC 页码，供 `CalcContext.save()` 调用。"""
    return _run_coroutine_sync(calculate_toc_page_numbers(document_url))


def _run_coroutine_sync(coroutine):
    """在同步调用方中执行协程；已处于事件循环时提示改用 async API。"""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _sync_loop_runner.run(coroutine)

    coroutine.close()
    raise RuntimeError(
        "calculate_toc_page_numbers_sync() cannot run inside an active event loop; "
        "use calculate_toc_page_numbers() instead."
    )


class _SyncLoopRunner:
    """为同步入口复用一个后台事件循环执行协程。"""

    def __init__(self):
        """初始化后台事件循环状态。"""
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ready_event = threading.Event()
        self._startup_error: BaseException | None = None

    def run(self, coroutine: Coroutine[object, object, _T]) -> _T:
        """在后台事件循环中执行协程并返回结果。"""
        self._ensure_started()
        if self._startup_error is not None:
            raise self._startup_error
        if self._loop is None:
            raise RuntimeError("Sync event loop did not start")

        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        return future.result()

    def _ensure_started(self):
        """按需启动后台事件循环。"""
        with self._lock:
            if self._thread is not None:
                return

            self._ready_event.clear()
            self._startup_error = None
            self._thread = threading.Thread(
                target=self._run_loop,
                name="uzoncalc-sync-asyncio",
                daemon=True,
            )
            self._thread.start()

        self._ready_event.wait()

    def _run_loop(self):
        """后台线程入口：创建并运行事件循环。"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self._loop = loop
        except BaseException as exc:
            self._startup_error = exc
            self._ready_event.set()
            loop.close()
            return

        self._ready_event.set()
        try:
            loop.run_forever()
        finally:
            loop.close()


_sync_loop_runner = _SyncLoopRunner()


def fill_toc_page_numbers(html_text: str, page_numbers: dict[str, int]) -> str:
    """将页码映射回写到目录页码节点。"""
    if not page_numbers or "toc-page" not in html_text:
        return html_text

    parser = _TocPageFillParser(page_numbers)
    parser.feed(html_text)
    parser.close()
    return parser.render()


@dataclass
class _OpenTocPage:
    should_replace: bool
    page_number: int | None
    skipped_content: bool = False


class _TocPageFillParser(HTMLParser):
    """流式回写 `.toc-page[data-heading-id]` 的文本和占位属性。"""

    def __init__(self, page_numbers: dict[str, int]):
        super().__init__(convert_charrefs=False)
        self.page_numbers = page_numbers
        self.output_parts: list[str] = []
        self.open_toc_pages: list[_OpenTocPage] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        heading_id = self._resolve_toc_heading_id(attrs)
        page_number = self.page_numbers.get(heading_id or "")
        should_replace = tag.lower() == "span" and page_number is not None
        if should_replace:
            attrs = [
                (name, value)
                for name, value in attrs
                if name.lower() != "data-page-placeholder"
            ]

        self.output_parts.append(self._render_start_tag(tag, attrs))
        self.open_toc_pages.append(
            _OpenTocPage(should_replace=should_replace, page_number=page_number)
        )

    def handle_endtag(self, tag: str):
        open_toc_page = self.open_toc_pages.pop() if self.open_toc_pages else None
        if open_toc_page and open_toc_page.should_replace:
            self.output_parts.append(str(open_toc_page.page_number))
        self.output_parts.append(f"</{tag}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]):
        self.output_parts.append(self._render_start_tag(tag, attrs, True))

    def handle_data(self, data: str):
        if self._is_replacing_toc_page():
            return
        self.output_parts.append(data)

    def handle_entityref(self, name: str):
        if self._is_replacing_toc_page():
            return
        self.output_parts.append(f"&{name};")

    def handle_charref(self, name: str):
        if self._is_replacing_toc_page():
            return
        self.output_parts.append(f"&#{name};")

    def handle_comment(self, data: str):
        self.output_parts.append(f"<!--{data}-->")

    def handle_decl(self, decl: str):
        self.output_parts.append(f"<!{decl}>")

    def handle_pi(self, data: str):
        self.output_parts.append(f"<?{data}>")

    def unknown_decl(self, data: str):
        self.output_parts.append(f"<![{data}]>")

    def render(self) -> str:
        """返回回写后的 HTML。"""
        return "".join(self.output_parts)

    def _is_replacing_toc_page(self) -> bool:
        return bool(self.open_toc_pages and self.open_toc_pages[-1].should_replace)

    def _resolve_toc_heading_id(
        self, attrs: list[tuple[str, str | None]]
    ) -> str | None:
        attr_values = {name.lower(): value for name, value in attrs}
        class_names = (attr_values.get("class") or "").split()
        if "toc-page" not in class_names:
            return None
        return attr_values.get("data-heading-id")

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
