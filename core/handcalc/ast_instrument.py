import ast
import inspect
import textwrap
from types import FunctionType
from typing import Any, Callable, Dict

from core.handcalc.ast_visitor import AstNodeVisitor
from core.handcalc.field_names import FieldNames
from core.handcalc.instrument_cache import InstrumentCache
from core.handcalc.exceptions import InstrumentationError
from core.handcalc.ast_validator import validate_ast


def instrument_function(func: Callable[..., Any]) -> FunctionType:
    """
    返回插桩后的函数。
    """
    # 如果传进来的本身就是插桩后的函数，直接返回
    if getattr(func, FieldNames.uzon_instrumented, False):
        return func  # type: ignore[return-value]

    # 使用缓存管理器：同一个原函数对象只插桩一次
    cache = InstrumentCache.get_instance()
    cached = cache.get(func)
    if cached is not None:
        return cached

    # 获取源码并去除非必要缩进
    try:
        src = textwrap.dedent(inspect.getsource(func))
        mod = ast.parse(src)
    except Exception as e:
        raise InstrumentationError(
            f"Failed to parse source of function {func.__name__}: {e}"
        ) from e

    # 关键：inspect.getsource 会包含原函数装饰器（如 @uzon_calc()）。
    # 如果不移除，exec 编译后的代码会再次应用装饰器，导致 wrapper 套娃递归，
    # 从而出现 "sheet() takes 2 positional arguments but N were given"。
    for node in mod.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == func.__name__
        ):
            node.decorator_list = []
            break

    # 调用所有的 visitor 进行处理
    ast_visitor = AstNodeVisitor()
    mod = ast_visitor.visit(mod)

    # 验证插桩后的 AST 安全性
    validate_ast(mod)

    # 编译前的"补位",确保 AST 节点信息完整
    ast.fix_missing_locations(mod)

    # 编译插桩后的代码
    try:
        code = compile(
            mod, filename=inspect.getsourcefile(func) or "<instrumented>", mode="exec"
        )
    except Exception as e:
        raise InstrumentationError(
            f"Failed to compile instrumented function {func.__name__}: {e}"
        ) from e

    glb: Dict[str, Any] = dict(func.__globals__)
    glb.update(__get_inject_globals())

    loc: Dict[str, Any] = {}
    # 真正执行编译后的代码：这一步会运行模块级语句，通常会把被插桩后的函数定义放进 loc
    try:
        exec(code, glb, loc)
    except Exception as e:
        raise InstrumentationError(
            f"Failed to execute instrumented code for {func.__name__}: {e}"
        ) from e

    new_func = loc.get(func.__name__)
    if not isinstance(new_func, FunctionType):
        raise InstrumentationError(
            f"instrument_function: failed to rebuild function {func.__name__}"
        )

    # 打标记：避免对"插桩后的函数"重复插桩
    try:
        setattr(new_func, FieldNames.uzon_instrumented, True)
    except Exception:
        # 某些情况下无法设置属性，忽略
        pass

    # 缓存并返回
    cache.set(func, new_func)
    return new_func


def __get_inject_globals():
    """
    获取插桩时需要注入的全局变量表。
    """
    # 注入记录步骤的函数
    from core.handcalc import recorder
    from core.handcalc import ir as uzon_ir
    from core.handcalc import steps as uzon_steps

    return {
        FieldNames.uzon_record_step: recorder.record_step,
        FieldNames.uzon_ir: uzon_ir,
        FieldNames.uzon_steps: uzon_steps,
    }
