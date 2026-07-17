"""Tests for document-export protocol boundaries."""

from __future__ import annotations

from pathlib import Path

from uzoncalc.context import CalcContext
from uzoncalc.exporting import HtmlDocumentExporter


class StubDocumentExporter:
    """Capture exported documents without writing to the filesystem."""

    def __init__(self) -> None:
        """Initialize the captured export list."""
        self.exports: list[tuple[str, str]] = []

    def export(self, html: str, path: str) -> None:
        """Capture one export call."""
        self.exports.append((html, path))


class StubTocResolver:
    """Provide deterministic page numbers for exporter tests."""

    def __init__(self) -> None:
        """Initialize the captured document URL."""
        self.document_url: str | None = None

    def calculate(self, document_url: str) -> dict[str, int]:
        """Return a deterministic page-number mapping."""
        self.document_url = document_url
        return {"heading-0": 2}

    def fill(self, html: str, page_numbers: dict[str, int]) -> str:
        """Replace the representative placeholder with its page number."""
        return html.replace(">placeholder<", f">{page_numbers['heading-0']}<")


def test_calc_context_delegates_save_to_document_exporter() -> None:
    """CalcContext should remain a facade over its export strategy."""
    exporter = StubDocumentExporter()
    context = CalcContext(document_exporter=exporter)

    context.save("report.html")

    assert exporter.exports == [(context.html(), "report.html")]


def test_html_exporter_resolves_toc_placeholders(tmp_path: Path) -> None:
    """The default HTML exporter should delegate ToC page resolution."""
    resolver = StubTocResolver()
    exporter = HtmlDocumentExporter(resolver)
    destination = tmp_path / "report.html"

    exporter.export(
        '<span data-page-placeholder="true">placeholder</span>', str(destination)
    )

    assert destination.read_text("utf-8") == (
        '<span data-page-placeholder="true">2</span>'
    )
    assert resolver.document_url == destination.resolve().as_uri()
