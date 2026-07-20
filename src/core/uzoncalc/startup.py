import asyncio
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from functools import wraps
import inspect
from typing import Any, ParamSpec, TypeVar, cast, overload

from .context import CalcContext
from .handcalc.ast_instrument import instrument_function
from .globals import _calc_instance, get_current_instance

from .units import unit

_PARAM_CTX = "ctx"
_PARAM_DEFAULTS = "defaults"
_PARAM_UNIT = "unit"
_MARKER_CALC_ENTRY = "_uzon_calc_entry"
_MARKER_CALC_FUNC = "_uzon_calc_func"
_P = ParamSpec("_P")
_R = TypeVar("_R")


@asynccontextmanager
async def uzon_calc_core(
    ctx_name: str | None = None,
    file_path: str | None = None,
    is_silent: bool = True,
    ctx_hook_created: Callable[[CalcContext], Any] | None = None,
):
    # 生成一个上下文实例
    inst = CalcContext(
        name=ctx_name,
        file_path=file_path,
        is_silent=is_silent,
        ctx_hook_created=ctx_hook_created,
    )
    token = _calc_instance.set(inst)
    try:
        yield inst
    finally:
        # 退出上下文
        inst.exit()
        _calc_instance.reset(token)


def _is_keyword_injectable_parameter(sig: inspect.Signature, param_name: str) -> bool:
    """判断参数是否可以通过关键字自动注入。

    Args:
        sig: 目标函数签名。
        param_name: 待检查的参数名称。

    Returns:
        若参数存在且支持关键字传参则返回 True，否则返回 False。

    Raises:
        None.
    """
    parameter = sig.parameters.get(param_name)
    if parameter is None:
        return False
    return parameter.kind in (
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    )


def _prepare_contextual_kwargs(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    ctx: CalcContext,
    sig: inspect.Signature,
    *,
    include_defaults: bool,
    filter_unknown: bool,
) -> dict[str, Any]:
    """准备带有当前计算上下文的关键字参数。

    Args:
        args: 调用方传入的位置参数。
        kwargs: 调用方传入的关键字参数。
        ctx: 当前计算上下文。
        sig: 目标函数签名。
        include_defaults: 是否消费 defaults 并写入上下文变量。
        filter_unknown: 是否过滤目标函数签名之外的关键字参数。

    Returns:
        可安全传递给目标函数的关键字参数副本。

    Raises:
        TypeError: 当调用参数无法按目标函数签名绑定时抛出。
    """
    merged = dict(kwargs)

    # 提取并设置 defaults 到 context.vars
    # 格式: {"title": {"field": value}, "defaults": {"field": value}}
    if include_defaults and _PARAM_DEFAULTS in merged:
        defaults = merged.pop(_PARAM_DEFAULTS)
        ctx.vars = defaults

    if filter_unknown:
        merged = {k: v for k, v in merged.items() if k in sig.parameters}

    bound = sig.bind_partial(*args, **merged)
    contextual_values = {
        _PARAM_CTX: ctx,
        _PARAM_UNIT: unit,
    }
    for param_name, param_value in contextual_values.items():
        if param_name in bound.arguments:
            continue
        if not _is_keyword_injectable_parameter(sig, param_name):
            continue
        merged[param_name] = param_value
        bound.arguments[param_name] = param_value

    return merged


def _instrument_with_signature(
    fn: Callable[..., Any],
) -> tuple[Callable[..., Any], inspect.Signature]:
    """对目标函数执行插桩并返回插桩函数签名。

    Args:
        fn: 待插桩的目标函数。

    Returns:
        插桩后的函数及其签名。

    Raises:
        Exception: 当底层 AST 插桩失败时透传异常。
    """
    instrumented_fn = instrument_function(fn)
    return instrumented_fn, inspect.signature(instrumented_fn)


def _get_current_instance_or_none() -> CalcContext | None:
    """获取当前计算上下文，不存在时返回 None。

    Args:
        None.

    Returns:
        当前计算上下文；若当前调用栈不在计算上下文中则返回 None。

    Raises:
        None.
    """
    return _calc_instance.get()


async def _call_contextual_async(
    instrumented_fn: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    ctx: CalcContext,
    sig: inspect.Signature,
    *,
    include_defaults: bool,
    filter_unknown: bool,
) -> Any:
    """在指定计算上下文中调用异步插桩函数。

    Args:
        instrumented_fn: 已插桩的异步函数。
        args: 调用方传入的位置参数。
        kwargs: 调用方传入的关键字参数。
        ctx: 当前计算上下文。
        sig: 插桩函数签名。
        include_defaults: 是否消费 defaults 并写入上下文变量。
        filter_unknown: 是否过滤目标函数签名之外的关键字参数。

    Returns:
        插桩函数的异步返回值。

    Raises:
        TypeError: 当调用参数无法按目标函数签名绑定时抛出。
        Exception: 目标函数执行期间抛出的异常会原样透传。
    """
    prepared_kwargs = _prepare_contextual_kwargs(
        args,
        kwargs,
        ctx,
        sig,
        include_defaults=include_defaults,
        filter_unknown=filter_unknown,
    )
    return await instrumented_fn(*args, **prepared_kwargs)


def _call_contextual_sync(
    instrumented_fn: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    ctx: CalcContext,
    sig: inspect.Signature,
    *,
    include_defaults: bool,
    filter_unknown: bool,
) -> Any:
    """在指定计算上下文中调用同步插桩函数。

    Args:
        instrumented_fn: 已插桩的同步函数。
        args: 调用方传入的位置参数。
        kwargs: 调用方传入的关键字参数。
        ctx: 当前计算上下文。
        sig: 插桩函数签名。
        include_defaults: 是否消费 defaults 并写入上下文变量。
        filter_unknown: 是否过滤目标函数签名之外的关键字参数。

    Returns:
        插桩函数的同步返回值。

    Raises:
        TypeError: 当调用参数无法按目标函数签名绑定时抛出。
        Exception: 目标函数执行期间抛出的异常会原样透传。
    """
    prepared_kwargs = _prepare_contextual_kwargs(
        args,
        kwargs,
        ctx,
        sig,
        include_defaults=include_defaults,
        filter_unknown=filter_unknown,
    )
    return instrumented_fn(*args, **prepared_kwargs)


def _mark_as_entry(func: Callable) -> Callable:
    """标记函数被 uzon_calc 装饰"""
    # 避免 pytest 将计算入口误识别为普通测试函数
    setattr(func, "__test__", False)
    setattr(func, _MARKER_CALC_ENTRY, True)
    return func


def _mark_as_calc_func(func: Callable[_P, _R]) -> Callable[_P, _R]:
    """标记函数被 uzon_calc_func 装饰。

    Args:
        func: 被标记的包装函数。

    Returns:
        原包装函数，便于链式返回。

    Raises:
        None.
    """
    setattr(func, "__test__", False)
    setattr(func, _MARKER_CALC_FUNC, True)
    return func


# 装饰器形式使用 uzon_calc
# 只支持异步函数
def uzon_calc(
    name: str | None = None,
) -> Callable[
    [Callable[_P, Awaitable[_R]]],
    Callable[_P, Awaitable[CalcContext | _R]],
]:
    """Decorate an async calculation entry while preserving its parameters."""

    def deco(
        fn: Callable[_P, Awaitable[_R]],
    ) -> Callable[_P, Awaitable[CalcContext | _R]]:
        # 获取函数所在文件的路径
        file_path = inspect.getfile(fn)

        # 对被装饰函数进行插桩，解析公式，赋值，字符串等
        instrumented_fn, sig = _instrument_with_signature(fn)

        # 只支持异步函数
        if not inspect.iscoroutinefunction(instrumented_fn):
            raise TypeError(f"Function {fn.__name__} must be async")

        @wraps(fn)
        async def async_wrapper(
            *args: _P.args, **kwargs: _P.kwargs
        ) -> CalcContext | _R:
            is_silent = cast(bool, kwargs.pop("is_silent", True))
            ctx_hook_created = cast(
                Callable[[CalcContext], Any] | None,
                kwargs.pop("ctx_hook_created", None),
            )

            current_ctx = _get_current_instance_or_none()
            if current_ctx is not None:
                return await _call_contextual_async(
                    instrumented_fn,
                    args,
                    kwargs,
                    current_ctx,
                    sig,
                    include_defaults=True,
                    filter_unknown=True,
                )

            async with uzon_calc_core(
                name,
                file_path,
                is_silent=is_silent,
                ctx_hook_created=ctx_hook_created,
            ) as ctx:
                await _call_contextual_async(
                    instrumented_fn,
                    args,
                    kwargs,
                    ctx,
                    sig,
                    include_defaults=True,
                    filter_unknown=True,
                )
                return ctx

        return _mark_as_entry(async_wrapper)  # type: ignore[return-value]

    return deco


@overload
def uzon_calc_func(func: Callable[_P, _R]) -> Callable[_P, _R]: ...


@overload
def uzon_calc_func(
    func: None = None,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...


def uzon_calc_func(
    func: Callable[..., Any] | None = None,
) -> Callable[..., Any]:
    """装饰可在计算入口内部复用的纯插桩函数。

    Args:
        func: 可选的待装饰函数；为 None 时返回实际装饰器。

    Returns:
        已插桩的 helper 包装函数，或等待函数参数的装饰器。

    Raises:
        TypeError: 当调用参数无法按原函数签名绑定时抛出。
        Exception: 原函数或插桩函数执行期间抛出的异常会原样透传。
    """

    def deco(fn: Callable[..., Any]):
        """对 helper 函数执行一次插桩并返回包装函数。

        Args:
            fn: 待插桩的 helper 函数。

        Returns:
            保留原始签名的同步或异步包装函数。

        Raises:
            TypeError: 当调用参数无法按原函数签名绑定时抛出。
            Exception: 原函数或插桩函数执行期间抛出的异常会原样透传。
        """
        instrumented_fn, sig = _instrument_with_signature(fn)
        public_sig = inspect.signature(fn)

        if inspect.iscoroutinefunction(instrumented_fn):

            @wraps(fn)
            async def async_func_wrapper(*args, **kwargs):
                """执行异步 helper，在计算上下文中记录插桩内容。

                Args:
                    *args: 传给原 helper 的位置参数。
                    **kwargs: 传给原 helper 的关键字参数。

                Returns:
                    原 helper 的异步返回值；无上下文时为普通函数调用结果。

                Raises:
                    TypeError: 当调用参数无法按目标函数签名绑定时抛出。
                    Exception: 原函数或插桩函数执行期间抛出的异常会原样透传。
                """
                current_ctx = _get_current_instance_or_none()
                if current_ctx is None:
                    return await fn(*args, **kwargs)

                return await _call_contextual_async(
                    instrumented_fn,
                    args,
                    kwargs,
                    current_ctx,
                    sig,
                    include_defaults=False,
                    filter_unknown=False,
                )

            async_func_wrapper.__signature__ = public_sig  # type: ignore[attr-defined]
            return _mark_as_calc_func(async_func_wrapper)

        @wraps(fn)
        def func_wrapper(*args, **kwargs):
            """执行同步 helper，在计算上下文中记录插桩内容。

            Args:
                *args: 传给原 helper 的位置参数。
                **kwargs: 传给原 helper 的关键字参数。

            Returns:
                原 helper 的同步返回值；无上下文时为普通函数调用结果。

            Raises:
                TypeError: 当调用参数无法按目标函数签名绑定时抛出。
                Exception: 原函数或插桩函数执行期间抛出的异常会原样透传。
            """
            current_ctx = _get_current_instance_or_none()
            if current_ctx is None:
                return fn(*args, **kwargs)

            return _call_contextual_sync(
                instrumented_fn,
                args,
                kwargs,
                current_ctx,
                sig,
                include_defaults=False,
                filter_unknown=False,
            )

        func_wrapper.__signature__ = public_sig  # type: ignore[attr-defined]
        return _mark_as_calc_func(func_wrapper)

    if func is None:
        return deco
    return deco(func)


async def run(
    func: Callable[..., Any],
    *args: Any,
    defaults: dict[str, dict[str, Any]] | None = None,
    is_silent: bool = True,
    ctx_hook_created: Callable[[CalcContext], Any] | None = None,
    **kwargs: Any,
) -> CalcContext:
    """
    异步函数运行器

    只支持异步函数（async def）

    Args:
        func: 要执行的异步函数
        *args: 位置参数
        defaults: 默认值字典，格式为 {"title": {"field": value}}
                  会保存到 context.vars 中
        is_silent: 是否静默执行，True 表示静默执行（默认）
        **kwargs: 关键字参数

    Returns:
        CalcContext 上下文对象
    """
    # 将 defaults 和 execution_mode 传递给被装饰的函数
    if defaults is not None:
        kwargs["defaults"] = defaults
    kwargs["is_silent"] = is_silent
    kwargs["ctx_hook_created"] = ctx_hook_created

    result = func(*args, **kwargs)

    if not inspect.iscoroutine(result):
        raise TypeError(f"Function {func.__name__} must be async")
    return await result


def run_sync(
    func: Callable[..., Any],
    *args: Any,
    defaults: dict[str, dict[str, Any]] | None = None,
    **kwargs: Any,
) -> CalcContext:
    """
    同步执行异步函数（静默模式）

    使用 asyncio.run() 执行异步函数
    在此模式下，UI 调用将直接返回默认值而不等待用户输入

    Args:
        func: 要执行的异步函数
        *args: 位置参数
        defaults: 默认值字典，格式为 {"title": {"field": value}, "defaults": {"field": value}}
                  会保存到 context.vars 中
        **kwargs: 关键字参数

    Returns:
        CalcContext 上下文对象
    """
    # 强制设置为 sync 模式，静默执行
    return asyncio.run(run(func, *args, defaults=defaults, is_silent=True, **kwargs))


def view(
    func: Callable[..., Any],
    *args: Any,
    defaults: dict[str, dict[str, Any]] | None = None,
    preferred_port: int = 0,
    **kwargs: Any,
) -> None:
    from .http_server import DEFAULT_SERVER_PORT, serve_static_html
    from .template.utils import render_html_template

    """执行计算函数并启动无文件监听的本地 HTML 预览服务。"""
    # 先按静默模式执行计算函数，再渲染完整 HTML
    ctx = run_sync(func, *args, defaults=defaults, **kwargs)
    html_output = render_html_template(ctx.html_content(), ctx.options)

    # 预览服务会自动从首选端口开始查找可用端口
    serve_static_html(html_output, preferred_port or DEFAULT_SERVER_PORT)
