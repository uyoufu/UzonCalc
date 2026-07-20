"""Helpers for reporting missing optional UzonCalc dependencies."""

from __future__ import annotations


class OptionalDependencyError(ImportError):
    """Report that a feature-specific dependency extra is not installed."""


def missing_optional_dependency(
    extra: str, cause: ImportError
) -> OptionalDependencyError:
    """Build an actionable error for an unavailable optional dependency.

    Args:
        extra: Name of the UzonCalc dependency extra.
        cause: Original import failure.

    Returns:
        Error containing the installation command for the requested feature.

    Raises:
        No exceptions are intentionally raised.
    """
    return OptionalDependencyError(
        f"This feature requires optional dependencies. "
        f"Install them with `pip install 'uzoncalc[{extra}]'`."
    )
