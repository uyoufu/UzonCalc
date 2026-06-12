from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from markdown_it_pyrs import MarkdownIt

markdown_instance: MarkdownIt | None = None


def get_markdown() -> MarkdownIt:
    """
    获取MarkdownIt实例
    """
    global markdown_instance
    if markdown_instance is None:
        from markdown_it_pyrs import MarkdownIt

        markdown_instance = MarkdownIt("commonmark").enable("table")

    return markdown_instance
