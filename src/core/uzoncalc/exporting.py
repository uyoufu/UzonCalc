"""Document export boundaries used by calculation contexts."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class TocPageNumberResolver(Protocol):
    """Resolve and apply printed page numbers for table-of-contents entries."""

    def calculate(self, document_url: str) -> dict[str, int]:
        """Calculate heading page numbers for a rendered document URL.

        Args:
            document_url: URL loaded by the print renderer.

        Returns:
            Mapping from heading identifiers to 1-based page numbers.
        """
        ...

    def fill(self, html: str, page_numbers: dict[str, int]) -> str:
        """Apply calculated page numbers to ToC placeholders.

        Args:
            html: Rendered HTML containing ToC placeholders.
            page_numbers: Heading identifiers mapped to page numbers.

        Returns:
            HTML with available page numbers filled in.
        """
        ...


class DocumentExporter(Protocol):
    """Persist a rendered HTML calculation document."""

    def export(self, html: str, path: str) -> None:
        """Write a rendered document to the requested path.

        Args:
            html: Complete rendered HTML.
            path: Destination file path.

        Returns:
            None.
        """
        ...


class DefaultTocPageNumberResolver:
    """Load the optional ToC implementation only when page numbers are needed."""

    def calculate(self, document_url: str) -> dict[str, int]:
        """Calculate heading page numbers through the optional ToC service."""
        from .service.toc_page_numbers import calculate_toc_page_numbers_sync

        return calculate_toc_page_numbers_sync(document_url)

    def fill(self, html: str, page_numbers: dict[str, int]) -> str:
        """Fill ToC placeholders through the lightweight HTML transformer."""
        from .service.toc_page_numbers import fill_toc_page_numbers

        return fill_toc_page_numbers(html, page_numbers)


class HtmlDocumentExporter:
    """Write HTML and optionally resolve printed ToC page numbers."""

    def __init__(self, toc_resolver: TocPageNumberResolver | None = None) -> None:
        """Initialize the exporter with an optional ToC resolver.

        Args:
            toc_resolver: Resolver used when the HTML contains page placeholders.

        Returns:
            None.

        Raises:
            No exceptions are intentionally raised.
        """
        self._toc_resolver = toc_resolver or DefaultTocPageNumberResolver()

    def export(self, html: str, path: str) -> None:
        """Write HTML and replace ToC placeholders when present.

        Args:
            html: Fully rendered HTML document.
            path: Destination file path.

        Returns:
            None.

        Raises:
            OSError: If the destination cannot be written.
            ImportError: If ToC dependencies are required but unavailable.
        """
        destination = Path(path)
        destination.write_text(html, encoding="utf-8")
        if 'data-page-placeholder="true"' not in html:
            return

        page_numbers = self._toc_resolver.calculate(destination.resolve().as_uri())
        destination.write_text(
            self._toc_resolver.fill(html, page_numbers),
            encoding="utf-8",
        )


__all__ = [
    "DefaultTocPageNumberResolver",
    "DocumentExporter",
    "HtmlDocumentExporter",
    "TocPageNumberResolver",
]
