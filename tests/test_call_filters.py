"""Tests for deterministic AST call-filter registries."""

from __future__ import annotations

import ast

import pytest

from uzoncalc.handcalc.call_filters import CallFilterError, CallFilterRegistry


def _parse_call(source: str) -> ast.Call:
    """Parse one expression call for registry tests."""
    expression = ast.parse(source, mode="eval").body
    assert isinstance(expression, ast.Call)
    return expression


def test_registry_snapshot_isolated_from_later_registration() -> None:
    """A traversal snapshot should not change during instrumentation."""
    registry = CallFilterRegistry()
    snapshot = registry.snapshot()

    registry.register_simple("LaterRegistered")

    assert registry.should_hide_call(_parse_call("LaterRegistered()"))
    assert not snapshot.should_hide_call(_parse_call("LaterRegistered()"))


def test_advanced_filter_error_includes_source_location() -> None:
    """Custom filter failures should retain their AST source location."""
    registry = CallFilterRegistry()

    def failing_filter(node: ast.Call) -> bool:
        """Raise a representative custom-filter failure."""
        raise ValueError("invalid filter")

    registry.register_advanced(failing_filter)
    call = _parse_call("custom()")

    with pytest.raises(CallFilterError, match=r"line 1, column 0"):
        registry.should_hide_call(call)
