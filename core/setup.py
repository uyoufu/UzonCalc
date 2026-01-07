from contextvars import ContextVar
from contextlib import contextmanager
from functools import wraps
import inspect

from core.context import CalcContext
from core.handcalc.ast_instrument import instrument_function

from core.units import unit

_calc_instance = ContextVar[CalcContext | None]("calc_ctx", default=None)


def get_current_instance():
    inst = _calc_instance.get()
    if inst is None:
        raise RuntimeError("no current instance in this context")
    return inst


@contextmanager
def uzon_calc_core(ctx_name: str | None = None):
    # 生成一个上下文实例
    inst = CalcContext(name=ctx_name)
    token = _calc_instance.set(inst)
    try:
        yield inst
    finally:
        _calc_instance.reset(token)


# 装饰器形式使用 uzon_calc
# 同时支持异步与同步函数
def uzon_calc(name: str | None = None):
    def deco(fn):
        # 对被装饰函数进行插桩，解析公式，赋值，字符串等
        instrumented_fn = instrument_function(fn)

        sig = inspect.signature(instrumented_fn)

        def _prepare_valid_kwargs(kwargs: dict, ctx: CalcContext) -> dict:
            # 在命名参数中，注入 ctx / unit，并过滤多余参数
            merged = dict(kwargs)
            merged["ctx"] = ctx
            merged["unit"] = unit
            return {k: v for k, v in merged.items() if k in sig.parameters}

        # 判断是否为异步函数
        if inspect.iscoroutinefunction(instrumented_fn):

            @wraps(fn)
            async def coroutine_wrapper(*args, **kwargs):
                with uzon_calc_core(name) as ctx:
                    valid_kwargs = _prepare_valid_kwargs(kwargs, ctx)
                    await instrumented_fn(*args, **valid_kwargs)

                    return ctx

            return coroutine_wrapper

        else:

            @wraps(fn)
            def wrapper(*args, **kwargs):

                with uzon_calc_core(name) as ctx:
                    valid_kwargs = _prepare_valid_kwargs(kwargs, ctx)
                    instrumented_fn(*args, **valid_kwargs)
                    return ctx

            return wrapper

    return deco
