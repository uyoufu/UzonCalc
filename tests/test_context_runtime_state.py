"""Regression tests for calculation-context runtime state."""

from __future__ import annotations

import asyncio

import pytest

from uzoncalc.context import CalcContext
from uzoncalc.interaction import InteractionState


def test_empty_inline_block_resets_inline_mode() -> None:
    """Ending an empty inline block should restore normal content recording."""
    context = CalcContext()

    context.start_inline(" | ")
    context.end_inline()
    context.append_content("after")

    assert not context.is_inline_mode
    assert context.contents == ["after"]


def test_repeated_start_inline_keeps_original_separator() -> None:
    """A nested start call should not mutate an active inline block."""
    context = CalcContext()

    context.start_inline(" | ")
    context.append_content("first")
    context.start_inline(" changed ")
    context.append_content("second")
    context.end_inline()

    assert context.contents == ["<p>first | second</p>"]


def test_result_future_cannot_replace_pending_consumer() -> None:
    """Replacing a pending result future should fail explicitly."""

    async def exercise() -> None:
        state = InteractionState()
        state.set_result_future(asyncio.get_running_loop().create_future())

        with pytest.raises(RuntimeError, match="pending result future"):
            state.set_result_future(asyncio.get_running_loop().create_future())

    asyncio.run(exercise())


def test_input_future_is_reused_until_completed() -> None:
    """Repeated UI setup should reuse the same pending input future."""

    async def exercise() -> None:
        state = InteractionState()
        first = state.set_input_future()
        second = state.set_input_future()
        assert second is first

        state.set_inputs({"window": {"value": 1}})
        assert await first == {"window": {"value": 1}}
        assert state.set_input_future() is not first

    asyncio.run(exercise())
