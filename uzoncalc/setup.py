import asyncio
from contextvars import ContextVar
from contextlib import asynccontextmanager
from functools import wraps
import inspect
from typing import Any, Callable, Optional

from .context import CalcContext
from .handcalc.ast_instrument import instrument_function

from .units import unit

_calc_instance = ContextVar[CalcContext | None]("calc_ctx", default=None)


def get_current_instance():
    inst = _calc_instance.get()
    if inst is None:
        raise RuntimeError("no current instance in this context")
    return inst


@asynccontextmanager
async def uzon_calc_core(ctx_name: str | None = None, file_path: str | None = None):
    # 生成一个上下文实例
    inst = CalcContext(name=ctx_name, file_path=file_path)
    token = _calc_instance.set(inst)
    try:
        yield inst
    finally:
        # 退出上下文
        inst.exit()
        _calc_instance.reset(token)


def _prepare_valid_kwargs(
    kwargs: dict, ctx: CalcContext, sig: inspect.Signature
) -> dict:
    """在命名参数中，注入 ctx / unit，并过滤多余参数"""
    merged = dict(kwargs)

    # 提取并设置 defaults 到 context.vars
    # 格式: {"title": {"field": value}, "defaults": {"field": value}}
    if "defaults" in merged:
        defaults = merged.pop("defaults")
        ctx.vars = defaults

    merged["ctx"] = ctx
    merged["unit"] = unit
    return {k: v for k, v in merged.items() if k in sig.parameters}


def _mark_as_entry(func: Callable) -> Callable:
    """标记函数被 uzon_calc 装饰"""
    setattr(func, "_uzon_calc_entry", True)
    return func


# 装饰器形式使用 uzon_calc
# 只支持异步函数
def uzon_calc(name: str | None = None):
    def deco(fn):
        # 获取函数所在文件的路径
        file_path = inspect.getfile(fn)

        # 对被装饰函数进行插桩，解析公式，赋值，字符串等
        instrumented_fn = instrument_function(fn)

        sig = inspect.signature(instrumented_fn)

        # 只支持异步函数
        if not inspect.iscoroutinefunction(instrumented_fn):
            raise TypeError(f"Function {fn.__name__} must be async")

        @wraps(fn)
        async def async_wrapper(*args, **kwargs):
            async with uzon_calc_core(name, file_path) as ctx:
                valid_kwargs = _prepare_valid_kwargs(kwargs, ctx, sig)
                await instrumented_fn(*args, **valid_kwargs)
                return ctx

        return _mark_as_entry(async_wrapper)

    return deco


async def run(
    func: Callable, *args, defaults: Optional[dict] = None, **kwargs
) -> CalcContext:
    """
    异步函数运行器

    只支持异步函数（async def）

    Args:
        func: 要执行的异步函数
        *args: 位置参数
        defaults: 默认值字典，格式为 {"title": {"field": value}, "defaults": {"field": value}}
                  会保存到 context.vars["ui_defaults"] 中
        **kwargs: 关键字参数

    Returns:
        CalcContext 上下文对象
    """
    # 将 defaults 传递给被装饰的函数
    if defaults is not None:
        kwargs["defaults"] = defaults

    result = func(*args, **kwargs)

    # 只处理异步协程
    if inspect.iscoroutine(result):
        return await result
    else:
        raise TypeError(f"Function {func.__name__} must be async")


def run_sync(
    func: Callable, *args, defaults: Optional[dict] = None, **kwargs
) -> CalcContext:
    """
    同步执行异步函数

    使用 asyncio.run() 执行异步函数

    Args:
        func: 要执行的异步函数
        *args: 位置参数
        defaults: 默认值字典，格式为 {"title": {"field": value}, "defaults": {"field": value}}
                  会保存到 context.vars["ui_defaults"] 中
        **kwargs: 关键字参数

    Returns:
        CalcContext 上下文对象
    """
    return asyncio.run(run(func, *args, defaults=defaults, **kwargs))
