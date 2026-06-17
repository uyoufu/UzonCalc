import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/core"))

from uzoncalc.service.toc_page_numbers import (
    TOC_PAGE_NUMBERS_ROUTE,
    fill_toc_page_numbers,
    parse_toc_page_numbers_from_pdf,
    render_heading_marker,
)


def test_render_heading_marker_uses_stable_machine_text():
    """标题 marker 应包含稳定 heading id，供 PDF 文本解析定位。"""
    marker = render_heading_marker("heading-0")

    assert "UZONCALC_TOC_HEADING:heading-0" in marker
    assert 'aria-hidden="true"' in marker
    assert "color:transparent" in marker


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
                FakePage("UZONCALC_TOC_HEADING:heading-0"),
                FakePage("正文"),
                FakePage("UZONCALC_TOC_HEADING:heading-1"),
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

    monkeypatch.setattr("uzoncalc.toc_page_numbers.fitz.open", fake_open)

    page_numbers = parse_toc_page_numbers_from_pdf(b"pdf-bytes")

    assert page_numbers == {"heading-0": 1, "heading-1": 3}
    assert fake_document.close_count == 1


def test_toc_route_is_shared_between_cli_and_api():
    """CLI HTTP 与 API 应使用同一路由后缀，方便模板 JS 统一请求。"""
    assert TOC_PAGE_NUMBERS_ROUTE == "/api/v1/calc/toc-page-numbers"
