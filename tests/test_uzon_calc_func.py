"""Regression tests for pure helper instrumentation."""

import asyncio
import inspect
import ast
import re
import html

import pytest

from core.uzoncalc import run_sync, uzon_calc, uzon_calc_func
from core.uzoncalc.handcalc.instrument_cache import InstrumentCache
from tests.fixtures import uzon_calc_func_helpers as helpers


def _plain_text(content: str) -> str:
    """Return normalized text from rendered HTML/MathML content.

    Args:
        content: Rendered HTML or MathML fragment.

    Returns:
        Text content with tags removed and whitespace collapsed.

    Raises:
        re.error: If the fixed tag-matching pattern is invalid.
    """
    return html.unescape(re.sub(r"<[^>]+>", "", content)).replace(" ", "")


@uzon_calc()
async def calc_sheet_with_sync_helper():
    """Call a sync helper with positional, keyword, and default arguments.

    Args:
        None.

    Returns:
        None.

    Raises:
        RuntimeError: If calculation context setup fails.
    """
    first_result = helpers.multiply_and_record(2, 3)
    second_result = helpers.multiply_and_record(2, right_value=3, scale=4)
    final_result = first_result + second_result


@uzon_calc()
async def calc_sheet_with_async_helper():
    """Call an async helper and record its body in the current context.

    Args:
        None.

    Returns:
        None.

    Raises:
        RuntimeError: If calculation context setup fails.
    """
    incremented_value = await helpers.async_increment(4)
    final_value = incremented_value * 2


@uzon_calc()
async def calc_sheet_with_contextual_helper():
    """Call a helper that receives injected ``ctx`` and ``unit`` arguments.

    Args:
        None.

    Returns:
        None.

    Raises:
        RuntimeError: If calculation context setup fails.
    """
    injected_length = helpers.helper_with_contextual_args(5)


@uzon_calc()
async def calc_sheet_with_explicit_contextual_arg(ctx):
    """Call a contextual helper with an explicitly supplied context.

    Args:
        ctx: Current calculation context injected by ``@uzon_calc``.

    Returns:
        None.

    Raises:
        RuntimeError: If calculation context setup fails.
    """
    explicit_length = helpers.helper_with_contextual_args(7, ctx=ctx)


@uzon_calc()
async def calc_sheet_with_parameter_matrix(ctx):
    """Call helpers that exercise Python's function parameter kinds.

    Args:
        ctx: Current calculation context injected by ``@uzon_calc``.

    Returns:
        None.

    Raises:
        RuntimeError: If calculation context setup fails.
    """
    matrix_result = {
        "no_arg": helpers.no_arg_helper(),
        "positional_only": helpers.positional_only_helper(4),
        "default": helpers.multiply_and_record(2, 5),
        "keyword": helpers.multiply_and_record(2, right_value=5, scale=3),
        "varargs": helpers.varargs_helper(1, 2, 3),
        "keyword_only": helpers.keyword_only_helper(value=4),
        "mixed": helpers.mixed_signature_helper(
            1,
            2,
            3,
            4,
            scale=2,
            source="caller",
        ),
        "optional_context": helpers.optional_contextual_helper(9),
        "kwargs_only": helpers.kwargs_only_helper(custom_key=1),
        "kwargs_explicit": helpers.kwargs_only_helper(ctx=ctx, explicit_key=2),
        "async_mixed": await helpers.async_mixed_signature_helper(5, scale=4),
    }
    ctx.append_content(f"<p>matrix:{matrix_result!r}</p>")


runtime_error_call_log: list[str] = []


@uzon_calc()
async def nested_calc_entry_raises_runtime_error():
    """Raise a RuntimeError from inside an existing calculation context.

    Args:
        None.

    Returns:
        None.

    Raises:
        RuntimeError: Always raised to verify wrapper propagation.
    """
    runtime_error_call_log.append("called")
    raise RuntimeError("business runtime error")


@uzon_calc()
async def calc_sheet_with_nested_runtime_error():
    """Call a nested calc entry that raises a business RuntimeError.

    Args:
        None.

    Returns:
        None.

    Raises:
        RuntimeError: Always raised by the nested calculation entry.
    """
    await nested_calc_entry_raises_runtime_error()


def _extract_matrix_result(ctx) -> dict:
    """Extract the parameter-matrix result dictionary from rendered content.

    Args:
        ctx: Calculation context produced by ``calc_sheet_with_parameter_matrix``.

    Returns:
        Parsed matrix result dictionary.

    Raises:
        AssertionError: If the matrix marker is not present.
        SyntaxError: If the rendered Python literal cannot be parsed.
    """
    for content in ctx.contents:
        if content.startswith("<p>matrix:"):
            literal = content.removeprefix("<p>matrix:").removesuffix("</p>")
            return ast.literal_eval(literal)
    raise AssertionError("matrix result marker was not rendered")


def test_sync_helper_records_body_and_preserves_return_values():
    """Sync helpers record internal steps and keep normal return values."""
    ctx = run_sync(calc_sheet_with_sync_helper)
    plain_contents = [_plain_text(content) for content in ctx.contents]

    assert any(
        "product=leftvalue·rightvalue=2·3=6" in content
        for content in plain_contents
    )
    assert any(
        "scaledproduct=product·scale=6·4=24" in content
        for content in plain_contents
    )
    assert any(
        "finalresult=firstresult+secondresult=6+24=30" in content
        for content in plain_contents
    )


def test_async_helper_records_body_and_preserves_return_value():
    """Async helpers record internal steps and keep awaited return values."""
    ctx = run_sync(calc_sheet_with_async_helper)
    plain_contents = [_plain_text(content) for content in ctx.contents]

    assert any("nextvalue=value+1=4+1=5" in content for content in plain_contents)
    assert any(
        "finalvalue=incrementedvalue·2=5·2=10" in content
        for content in plain_contents
    )


def test_contextual_arguments_are_injected_only_when_unbound():
    """``ctx`` and ``unit`` are injected without affecting positional args."""
    ctx = run_sync(calc_sheet_with_contextual_helper)
    content = "\n".join(ctx.contents)
    plain_contents = [_plain_text(content) for content in ctx.contents]

    assert "<p>ctx-injected</p>" in content
    assert any(
        "injectedlength=helpers.helper_with_contextual_args(5)" in content
        for content in plain_contents
    )


def test_explicit_context_argument_is_not_injected_twice():
    """Explicit ``ctx`` keyword arguments are not duplicated by the wrapper."""
    ctx = run_sync(calc_sheet_with_explicit_contextual_arg)
    plain_contents = [_plain_text(content) for content in ctx.contents]

    assert any(
        "explicitlength=helpers.helper_with_contextual_args" in content
        for content in plain_contents
    )
    assert any("7mm" in content for content in plain_contents)


def test_parameter_matrix_preserves_python_call_semantics():
    """Common helper parameter shapes keep normal Python calling behavior."""
    ctx = run_sync(calc_sheet_with_parameter_matrix)
    matrix_result = _extract_matrix_result(ctx)

    assert matrix_result == {
        "no_arg": "no-arg",
        "positional_only": 8,
        "default": 10,
        "keyword": 30,
        "varargs": 6,
        "keyword_only": 12,
        "mixed": (20, ("source",)),
        "optional_context": (9, True, True),
        "kwargs_only": ("custom_key",),
        "kwargs_explicit": ("ctx", "explicit_key"),
        "async_mixed": 20,
    }


def test_kwargs_only_helper_does_not_receive_implicit_contextual_args():
    """Pure ``**kwargs`` helpers do not receive implicit ``ctx`` or ``unit``."""
    ctx = run_sync(calc_sheet_with_parameter_matrix)
    matrix_result = _extract_matrix_result(ctx)

    assert matrix_result["kwargs_only"] == ("custom_key",)
    assert "ctx" not in matrix_result["kwargs_only"]
    assert "unit" not in matrix_result["kwargs_only"]
    assert matrix_result["kwargs_explicit"] == ("ctx", "explicit_key")


def test_parameter_matrix_public_signatures_are_preserved():
    """Decorated helpers expose the same signatures as their wrapped functions."""
    helper_names = [
        "no_arg_helper",
        "positional_only_helper",
        "varargs_helper",
        "keyword_only_helper",
        "mixed_signature_helper",
        "optional_contextual_helper",
        "kwargs_only_helper",
        "async_mixed_signature_helper",
    ]

    for helper_name in helper_names:
        helper_func = getattr(helpers, helper_name)
        assert inspect.signature(helper_func) == inspect.signature(
            helper_func.__wrapped__
        )


def test_decorated_helper_keeps_public_signature_and_markers():
    """The decorated helper exposes the original signature and helper marker."""
    signature = inspect.signature(helpers.multiply_and_record)

    assert str(signature) == "(left_value: int, right_value: int, scale: int = 1) -> int"
    assert getattr(helpers.multiply_and_record, "_uzon_calc_func") is True
    assert not getattr(helpers.multiply_and_record, "_uzon_calc_entry", False)
    assert helpers.multiply_and_record.__test__ is False


def test_sync_helper_can_run_without_calculation_context():
    """Sync helpers run like normal Python functions without a context."""
    result = helpers.multiply_and_record(2, 3, scale=4)

    assert result == 24


def test_async_helper_can_run_without_calculation_context():
    """Async helpers run like normal Python coroutines without a context."""
    result = asyncio.run(helpers.async_increment(4))

    assert result == 5


def test_helpers_do_not_inject_contextual_args_without_calculation_context():
    """Helpers do not inject ``ctx`` or ``unit`` outside a calculation context."""
    optional_result = helpers.optional_contextual_helper(9)

    assert optional_result == (9, False, False)
    with pytest.raises(TypeError, match="required keyword-only argument"):
        helpers.helper_with_contextual_args(5)


def test_nested_calc_runtime_error_is_not_treated_as_missing_context():
    """Nested calc RuntimeError values propagate without creating a new context."""
    runtime_error_call_log.clear()

    with pytest.raises(RuntimeError, match="business runtime error"):
        run_sync(calc_sheet_with_nested_runtime_error)

    assert runtime_error_call_log == ["called"]


def test_instrument_cache_reuses_the_original_helper_function():
    """The original helper function is cached after decoration."""
    cache = InstrumentCache.get_instance()

    assert cache.get(helpers.multiply_and_record.__wrapped__) is not None


def test_uzon_calc_func_supports_parentheses_form():
    """The ``@uzon_calc_func()`` form applies the helper marker."""
    assert getattr(helpers.async_increment, "_uzon_calc_func") is True
