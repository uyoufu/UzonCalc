from __future__ import annotations

import numbers
from typing import Any

import pint

from .. import ir

_UNNORMALIZED = object()


def normalize_renderable_value(value: Any) -> Any | None:
    """Normalize a runtime value into a safe formula-display value.

    Args:
        value: Runtime value captured from user calculation code.

    Returns:
        A value that can be rendered without leaking object ``repr`` details, or
        ``None`` when the value should remain symbolic.

    Raises:
        No exceptions are intentionally propagated; conversion failures mark the
        value as not renderable.
    """
    if value is None:
        return None

    if isinstance(value, ir.MathNode):
        return value

    if isinstance(value, bool):
        return str(value)

    if isinstance(value, str):
        return value

    if isinstance(value, numbers.Integral):
        return int(value)

    if isinstance(value, numbers.Real):
        return float(value)

    if isinstance(value, pint.Quantity):
        return value

    if isinstance(value, (list, tuple)):
        return _normalize_sequence(value)

    sequence_value = _try_convert_to_sequence(value)
    if sequence_value is not _UNNORMALIZED:
        return normalize_renderable_value(sequence_value)

    return None


def _normalize_sequence(value: list[Any] | tuple[Any, ...]) -> list[Any] | None:
    """Normalize every element in a runtime sequence.

    Args:
        value: Runtime sequence that should be displayed as an array.

    Returns:
        A list containing normalized elements, or ``None`` if any element cannot
        be safely displayed.

    Raises:
        No exceptions are raised.
    """
    normalized_items: list[Any] = []
    for element in value:
        normalized_element = normalize_renderable_value(element)
        if normalized_element is None:
            return None
        normalized_items.append(normalized_element)
    return normalized_items


def _try_convert_to_sequence(value: Any) -> Any:
    """Convert array-like values through a safe no-argument sequence protocol.

    Args:
        value: Runtime value that might expose a ``tolist()`` conversion.

    Returns:
        The converted value, or an internal sentinel when conversion is not
        available or not trustworthy.

    Raises:
        No exceptions are raised.
    """
    tolist = getattr(value, "tolist", None)
    if not callable(tolist):
        return _UNNORMALIZED

    try:
        converted = tolist()
    except Exception:
        return _UNNORMALIZED

    if converted is value:
        return _UNNORMALIZED

    if isinstance(converted, (str, int, float, list, tuple)):
        return converted
    if isinstance(converted, numbers.Real) and not isinstance(converted, bool):
        return converted
    return _UNNORMALIZED
