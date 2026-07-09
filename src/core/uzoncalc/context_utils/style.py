"""Provide inline text style helpers for calculation documents.

The module exposes lowercase helpers that return HTML strings and uppercase
helpers that persist the generated HTML into the current calculation context.
"""

from __future__ import annotations

from .elements import P, h


def bold(content: str | list[str]) -> str:
    """Render inline bold text.

    Args:
        content: Text or trusted HTML fragments to wrap with a bold tag.
        persist: Whether to append the rendered fragment to the current context.

    Returns:
        HTML string wrapped in a bold tag.

    Raises:
        RuntimeError: Propagated when no calculation context is active.
    """
    return h("b", content)


def Bold(content: str | list[str]) -> None:
    """Persist inline bold text into the current calculation context.

    Args:
        content: Text or trusted HTML fragments to wrap with a bold tag.

    Returns:
        None.

    Raises:
        RuntimeError: Propagated when no calculation context is active.
    """
    P(bold(content))


def italic(content: str | list[str]) -> str:
    """Render inline italic text.

    Args:
        content: Text or trusted HTML fragments to wrap with an italic tag.
        persist: Whether to append the rendered fragment to the current context.

    Returns:
        HTML string wrapped in an italic tag.

    Raises:
        RuntimeError: Propagated when no calculation context is active.
    """
    return h("i", content)


def Italic(content: str | list[str]) -> None:
    """Persist inline italic text into the current calculation context.

    Args:
        content: Text or trusted HTML fragments to wrap with an italic tag.

    Returns:
        None.

    Raises:
        RuntimeError: Propagated when no calculation context is active.
    """
    P(italic(content))
