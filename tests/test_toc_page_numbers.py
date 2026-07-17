import asyncio
import sys
import threading
from types import SimpleNamespace

import pytest

from uzoncalc.http_server import HtmlPreviewState, create_html_server
from uzoncalc.service.toc_page_numbers import (
    TOC_PAGE_NUMBERS_ROUTE,
    _run_coroutine_sync,
    calculate_toc_page_numbers_sync,
    fill_toc_page_numbers,
    parse_toc_page_numbers_from_pdf,
    render_heading_marker,
)
from uzoncalc.service.playwright_service import close_playwright_service


def test_render_heading_marker_uses_stable_machine_text():
    """标题 marker 应包含稳定 heading id，供 PDF 文本解析定位。"""
    marker = render_heading_marker("heading-0")

    assert "UZONCALC_TOC_HEADING:heading-0|" in marker
    assert 'aria-hidden="true"' in marker
    assert "color:transparent" in marker
    assert "opacity:0" not in marker


def test_calculate_toc_page_numbers_reads_heading_markers_from_pdf():
    """页码应来自 PDF 中正文标题 marker 的实际页序。"""
    html = f"""
<!doctype html>
<html>
<head>
  <style>@page {{ size: A4; margin: 20mm; }}</style>
</head>
<body>
  <div id="toc">
    <span class="toc-page" data-heading-id="heading-0" data-page-placeholder="true">&nbsp;</span>
    <span class="toc-page" data-heading-id="heading-1" data-page-placeholder="true">&nbsp;</span>
  </div>
  <h2 id="heading-0">{render_heading_marker("heading-0")}正文标题</h2>
  <h3 id="heading-1">{render_heading_marker("heading-1")}Windows 平台说明</h3>
</body>
</html>
"""
    preview_state = HtmlPreviewState(html)
    server, selected_port = create_html_server(preview_state, preferred_port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        page_numbers = calculate_toc_page_numbers_sync(
            f"http://127.0.0.1:{selected_port}/"
        )
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()

    assert page_numbers == {"heading-0": 1, "heading-1": 1}


def test_calculate_toc_page_numbers_sync_rejects_running_event_loop():
    """同步页码入口不应在已有事件循环中嵌套执行。"""

    async def run_test():
        with pytest.raises(RuntimeError, match="use calculate_toc_page_numbers"):
            calculate_toc_page_numbers_sync("http://127.0.0.1:32180/")

    asyncio.run(run_test())


def test_calculate_toc_page_numbers_sync_reuses_default_service(monkeypatch):
    """同步页码入口连续调用时应复用 core 默认 Playwright 服务。"""
    created_services = []
    rendered_urls = []

    class FakePlaywrightService:
        """记录同步页码入口是否复用默认服务。"""

        def __init__(self):
            created_services.append(self)

        async def render_pdf_from_url(self, document_url: str) -> bytes:
            """模拟 PDF 渲染并记录调用 URL。"""
            rendered_urls.append(document_url)
            return b"pdf-bytes"

        async def close(self):
            """模拟默认服务关闭。"""
            return None

    _run_coroutine_sync(close_playwright_service())
    monkeypatch.setattr(
        "uzoncalc.service.playwright_service.PlaywrightService",
        FakePlaywrightService,
    )
    monkeypatch.setattr(
        "uzoncalc.service.toc_page_numbers.parse_toc_page_numbers_from_pdf",
        lambda pdf_bytes: {"heading-0": len(rendered_urls)},
    )

    assert calculate_toc_page_numbers_sync("http://127.0.0.1:first/") == {
        "heading-0": 1
    }
    assert calculate_toc_page_numbers_sync("http://127.0.0.1:second/") == {
        "heading-0": 2
    }

    assert rendered_urls == [
        "http://127.0.0.1:first/",
        "http://127.0.0.1:second/",
    ]
    assert len(created_services) == 1
    _run_coroutine_sync(close_playwright_service())


def test_fill_toc_page_numbers_updates_placeholders():
    """页码映射应回写目录页码并移除占位状态。"""
    html = """
<div id="toc">
  <span class="toc-page" data-heading-id="heading-0" data-page-placeholder="true">&nbsp;</span>
  <span class="toc-page" data-heading-id="heading-1" data-page-placeholder="true">&nbsp;</span>
</div>
"""

    updated = fill_toc_page_numbers(html, {"heading-0": 2})

    assert '<span class="toc-page" data-heading-id="heading-0">2</span>' in updated
    assert (
        '<span class="toc-page" data-heading-id="heading-1" '
        'data-page-placeholder="true">&nbsp;</span>'
    ) in updated


def test_parse_toc_page_numbers_from_pdf_uses_pymupdf(monkeypatch):
    """PDF 文本中的 marker 页序应转换为 1-based 页码。"""

    class FakePage:
        def __init__(self, text: str):
            self.text = text

        def get_text(self):
            """模拟 PyMuPDF Page.get_text()。"""
            return self.text

    class FakeDocument:
        def __init__(self):
            self.pages = [
                FakePage("UZONCALC_TOC_HEADING:heading-0|"),
                FakePage("正文"),
                FakePage("UZONCALC_TOC_HEADING:heading-1|"),
            ]
            self.close_count = 0

        @property
        def page_count(self):
            """返回模拟 PDF 页数。"""
            return len(self.pages)

        def load_page(self, page_index: int):
            """按页索引返回模拟页面。"""
            return self.pages[page_index]

        def close(self):
            """记录 PDF 文档已关闭。"""
            self.close_count += 1

    fake_document = FakeDocument()

    def fake_open(*, stream, filetype):
        """模拟 fitz.open(stream=..., filetype='pdf')。"""
        assert stream == b"pdf-bytes"
        assert filetype == "pdf"
        return fake_document

    monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=fake_open))

    page_numbers = parse_toc_page_numbers_from_pdf(b"pdf-bytes")

    assert page_numbers == {"heading-0": 1, "heading-1": 3}
    assert fake_document.close_count == 1


def test_parse_toc_page_numbers_stops_before_adjacent_heading_text(monkeypatch):
    """marker 与英文标题粘连时不应把标题文本解析进 heading id。"""

    class FakePage:
        def get_text(self):
            """模拟 PDF 将 marker 与标题文本抽取为相邻文本。"""
            return "UZONCALC_TOC_HEADING:heading-1|Windows 平台说明"

    class FakeDocument:
        page_count = 1

        def load_page(self, page_index: int):
            """返回唯一的模拟页面。"""
            assert page_index == 0
            return FakePage()

        def close(self):
            """模拟关闭 PDF 文档。"""

    def fake_open(*, stream, filetype):
        """模拟 PyMuPDF 打开 PDF。"""
        return FakeDocument()

    monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=fake_open))

    assert parse_toc_page_numbers_from_pdf(b"pdf-bytes") == {"heading-1": 1}


def test_parse_toc_page_numbers_ignores_unterminated_marker(monkeypatch):
    """缺少终止符的旧 marker 不应把相邻标题文本误解析为 id。"""

    class FakePage:
        def get_text(self):
            """模拟旧 marker 与英文标题文本粘连后的 PDF 文本。"""
            return "UZONCALC_TOC_HEADING:heading-1Windows 平台说明"

    class FakeDocument:
        page_count = 1

        def load_page(self, page_index: int):
            """返回唯一的模拟页面。"""
            assert page_index == 0
            return FakePage()

        def close(self):
            """模拟关闭 PDF 文档。"""

    def fake_open(*, stream, filetype):
        """模拟 PyMuPDF 打开 PDF。"""
        return FakeDocument()

    monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=fake_open))

    assert parse_toc_page_numbers_from_pdf(b"pdf-bytes") == {}


def test_toc_route_is_shared_between_cli_and_api():
    """CLI HTTP 与 API 应使用同一路由后缀，方便模板 JS 统一请求。"""
    assert TOC_PAGE_NUMBERS_ROUTE == "/api/v1/calc/toc-page-numbers"
