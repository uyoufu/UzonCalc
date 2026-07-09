"""Helper functions used by ``tests.test_uzon_calc_func``."""

from core.uzoncalc import uzon_calc_func


@uzon_calc_func
def no_arg_helper() -> str:
    """Return a marker value from a helper without parameters.

    Args:
        None.

    Returns:
        A fixed marker value.

    Raises:
        RuntimeError: If called without an active calculation context.
    """
    marker = "no-arg"
    return marker


@uzon_calc_func
def positional_only_helper(value: int, /) -> int:
    """Return a value derived from a positional-only argument.

    Args:
        value: Positional-only value to double.

    Returns:
        The doubled value.

    Raises:
        RuntimeError: If called without an active calculation context.
    """
    doubled_value = value * 2
    return doubled_value


@uzon_calc_func
def multiply_and_record(left_value: int, right_value: int, scale: int = 1) -> int:
    """Return a scaled product while recording intermediate expressions.

    Args:
        left_value: Left operand for multiplication.
        right_value: Right operand for multiplication.
        scale: Scale factor applied to the product.

    Returns:
        The scaled product.

    Raises:
        RuntimeError: If called without an active calculation context.
    """
    product = left_value * right_value
    scaled_product = product * scale
    return scaled_product


@uzon_calc_func
def varargs_helper(*values: int) -> int:
    """Return the sum of variable positional arguments.

    Args:
        *values: Values to sum.

    Returns:
        Sum of all positional arguments.

    Raises:
        RuntimeError: If called without an active calculation context.
    """
    total_value = sum(values)
    return total_value


@uzon_calc_func
def keyword_only_helper(*, value: int) -> int:
    """Return a value derived from a keyword-only argument.

    Args:
        value: Keyword-only value to triple.

    Returns:
        The tripled value.

    Raises:
        RuntimeError: If called without an active calculation context.
    """
    tripled_value = value * 3
    return tripled_value


@uzon_calc_func
def mixed_signature_helper(
    left_value: int,
    /,
    right_value: int = 1,
    *extra_values: int,
    scale: int = 1,
    **metadata,
) -> tuple[int, tuple[str, ...]]:
    """Return a value from a mixed Python function signature.

    Args:
        left_value: Positional-only base value.
        right_value: Positional-or-keyword value.
        *extra_values: Additional positional values.
        scale: Keyword-only scale value.
        **metadata: Caller-provided metadata.

    Returns:
        A tuple containing the computed value and metadata keys.

    Raises:
        RuntimeError: If called without an active calculation context.
    """
    base_total = left_value + right_value + sum(extra_values)
    scaled_total = base_total * scale
    return scaled_total, tuple(sorted(metadata))


@uzon_calc_func
def optional_contextual_helper(value: int, ctx=None, unit=None):
    """Return whether optional contextual arguments were provided.

    Args:
        value: Value to pair with the context flags.
        ctx: Optional calculation context.
        unit: Optional unit registry.

    Returns:
        A tuple with the value and two context-presence flags.

    Raises:
        RuntimeError: If called without an active calculation context.
    """
    has_context = ctx is not None
    has_unit = unit is not None
    return value, has_context, has_unit


@uzon_calc_func
def kwargs_only_helper(**metadata) -> tuple[str, ...]:
    """Return the keys passed through ``**metadata``.

    Args:
        **metadata: Caller-provided keyword metadata.

    Returns:
        Sorted metadata keys.

    Raises:
        RuntimeError: If called without an active calculation context.
    """
    metadata_keys = tuple(sorted(metadata))
    return metadata_keys


@uzon_calc_func()
async def async_increment(value: int) -> int:
    """Return ``value + 1`` while recording the helper body.

    Args:
        value: Number to increment.

    Returns:
        The incremented value.

    Raises:
        RuntimeError: If called without an active calculation context.
    """
    next_value = value + 1
    return next_value


@uzon_calc_func()
async def async_mixed_signature_helper(value: int, /, *, scale: int = 1) -> int:
    """Return a scaled value from an async mixed-signature helper.

    Args:
        value: Positional-only value to scale.
        scale: Keyword-only scale factor.

    Returns:
        Scaled value.

    Raises:
        RuntimeError: If called without an active calculation context.
    """
    scaled_value = value * scale
    return scaled_value


@uzon_calc_func
def helper_with_contextual_args(value: int, *, ctx, unit):
    """Use automatically injected context and unit values.

    Args:
        value: Numeric millimeter magnitude.
        ctx: Current calculation context injected by ``@uzon_calc_func``.
        unit: Unit registry injected by ``@uzon_calc_func``.

    Returns:
        A quantity expressed in millimeters.

    Raises:
        RuntimeError: If called without an active calculation context.
    """
    length = value * unit.mm
    ctx.append_content("<p>ctx-injected</p>")
    return length
