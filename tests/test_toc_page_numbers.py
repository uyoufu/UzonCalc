import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/core"))

from uzoncalc.http_server import HtmlPreviewState, create_html_server
from uzoncalc.service.toc_page_numbers import (
    TOC_PAGE_NUMBERS_ROUTE,
    calculate_toc_page_numbers_sync,
    fill_toc_page_numbers,
    parse_toc_page_numbers_from_pdf,
    render_heading_marker,
)


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

        def __iter__(self):
            return iter(self.pages)

        def close(self):
            """记录 PDF 文档已关闭。"""
            self.close_count += 1

    fake_document = FakeDocument()

    def fake_open(*, stream, filetype):
        """模拟 fitz.open(stream=..., filetype='pdf')。"""
        assert stream == b"pdf-bytes"
        assert filetype == "pdf"
        return fake_document

    monkeypatch.setattr("uzoncalc.service.toc_page_numbers.fitz.open", fake_open)

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
        def __iter__(self):
            return iter([FakePage()])

        def close(self):
            """模拟关闭 PDF 文档。"""

    def fake_open(*, stream, filetype):
        """模拟 PyMuPDF 打开 PDF。"""
        return FakeDocument()

    monkeypatch.setattr("uzoncalc.service.toc_page_numbers.fitz.open", fake_open)

    assert parse_toc_page_numbers_from_pdf(b"pdf-bytes") == {"heading-1": 1}


def test_parse_toc_page_numbers_ignores_unterminated_marker(monkeypatch):
    """缺少终止符的旧 marker 不应把相邻标题文本误解析为 id。"""

    class FakePage:
        def get_text(self):
            """模拟旧 marker 与英文标题文本粘连后的 PDF 文本。"""
            return "UZONCALC_TOC_HEADING:heading-1Windows 平台说明"

    class FakeDocument:
        def __iter__(self):
            return iter([FakePage()])

        def close(self):
            """模拟关闭 PDF 文档。"""

    def fake_open(*, stream, filetype):
        """模拟 PyMuPDF 打开 PDF。"""
        return FakeDocument()

    monkeypatch.setattr("uzoncalc.service.toc_page_numbers.fitz.open", fake_open)

    assert parse_toc_page_numbers_from_pdf(b"pdf-bytes") == {}


def test_toc_route_is_shared_between_cli_and_api():
    """CLI HTTP 与 API 应使用同一路由后缀，方便模板 JS 统一请求。"""
    assert TOC_PAGE_NUMBERS_ROUTE == "/api/v1/calc/toc-page-numbers"
