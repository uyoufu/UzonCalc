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


def red(content: str | list[str]) -> str:
    """Render inline red text.

    Args:
        content: Text or trusted HTML fragments to wrap with a red tag.

    Returns:
        HTML string wrapped in a red tag.
    """
    return h("span", content, classes="text-red-500")


def Red(content: str | list[str]) -> None:
    """Persist inline red text into the current calculation context.

    Args:
        content: Text or trusted HTML fragments to wrap with a red tag.
    """
    P(red(content))


def green(content: str | list[str]) -> str:
    """Render inline green text.

    Args:
        content: Text or trusted HTML fragments to wrap with a green tag.

    Returns:
        HTML string wrapped in a green tag.
    """
    return h("span", content, classes="text-green-500")


def Green(content: str | list[str]) -> None:
    """Persist inline green text into the current calculation context."""
    P(green(content))


def yellow(content: str | list[str]) -> str:
    """Render inline yellow text.

    Args:
        content: Text or trusted HTML fragments to wrap with a yellow tag.

    Returns:
        HTML string wrapped in a yellow tag.
    """
    return h("span", content, classes="text-yellow-500")


def Yellow(content: str | list[str]) -> None:
    """Persist inline yellow text into the current calculation context."""
    P(yellow(content))


__all__ = [
    "Bold",
    "Green",
    "Italic",
    "Red",
    "Yellow",
    "bold",
    "green",
    "italic",
    "red",
    "yellow",
]
