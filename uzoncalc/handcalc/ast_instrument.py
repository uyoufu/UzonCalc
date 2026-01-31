import ast
import inspect
import textwrap
from types import FunctionType
from typing import Any, Callable, Dict

from .ast_visitor import AstNodeVisitor
from .field_names import FieldNames
from .instrument_cache import InstrumentCache
from .exceptions import InstrumentationError
from .ast_validator import validate_ast


def _calculate_line_offset(
    actual_first_lineno: int, ast_func_def_lineno: int
) -> int:
    """
    计算插桩后 AST 需要调整的行号偏移量。
    
    当使用 inspect.getsource + textwrap.dedent 获取并解析函数源码时，
    AST 中的行号会从 1 开始重新计数。但实际源文件中函数可能在任意行。
    此函数计算需要的偏移量以恢复正确的行号。
    
    参数:
        actual_first_lineno: 函数在源文件中的实际起始行号（通常是装饰器行或 def 行）
        ast_func_def_lineno: dedent 后 AST 中 FunctionDef 节点的 lineno（def 行）
    
    返回:
        行号偏移量。应用此偏移后，AST 中的行号将对应源文件中的实际行号。
    
    示例:
        源文件第 13 行: @decorator
        源文件第 14 行: def func():
        源文件第 15 行:     x = 1
        
        dedent 后 AST:
        第 1 行: @decorator
        第 2 行: def func():  <- ast_func_def_lineno = 2
        第 3 行:     x = 1
        
        actual_first_lineno = 13 (co_firstlineno 指向装饰器)
        偏移 = 13 - 2 + 1 = 12
        
        应用偏移后:
        第 13 行: @decorator  (1 + 12)
        第 14 行: def func(): (2 + 12)
        第 15 行:     x = 1   (3 + 12)
    """
    return actual_first_lineno - ast_func_def_lineno + 1


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

    # 移除装饰器以避免重复应用，同时保存行号信息用于后续调整
    # inspect.getsource 获取的源码包含装饰器（如 @uzon_calc()）
    # 如果不移除，exec 时会重复应用装饰器导致递归错误
    ast_func_def_lineno = None
    for node in mod.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == func.__name__
        ):
            # 保存 dedent 后 AST 中 def 关键字的行号
            ast_func_def_lineno = node.lineno
            # 移除装饰器列表
            node.decorator_list = []
            break

    # 调用所有的 visitor 进行处理
    ast_visitor = AstNodeVisitor()
    mod = ast_visitor.visit(mod)

    # 验证插桩后的 AST 安全性
    validate_ast(mod)

    # 编译前的"补位",确保 AST 节点信息完整
    # 注意：需要在调整行号之前调用，因为 increment_lineno 需要完整的位置信息
    ast.fix_missing_locations(mod)

    # 调整 AST 行号以匹配源文件中的实际位置
    # 这对于调试时的断点和错误堆栈信息至关重要
    if ast_func_def_lineno is not None:
        try:
            # co_firstlineno 指向函数的实际起始行（装饰器行或 def 行）
            actual_first_lineno = func.__code__.co_firstlineno
            # 计算并应用行号偏移
            lineno_offset = _calculate_line_offset(
                actual_first_lineno, ast_func_def_lineno
            )
            if lineno_offset != 0:
                ast.increment_lineno(mod, lineno_offset)
        except Exception:
            # 偏移计算失败时继续使用原始行号
            pass

    # 编译插桩后的代码，使用原始源文件路径以便调试器正确显示
    import os
    source_file = inspect.getsourcefile(func)
    filename = os.path.abspath(source_file) if source_file else "<instrumented>"
    
    try:
        code = compile(mod, filename=filename, mode="exec")
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
    from . import recorder
    from . import ir as uzon_ir
    from . import steps as uzon_steps

    return {
        FieldNames.uzon_record_step: recorder.record_step,
        FieldNames.uzon_ir: uzon_ir,
        FieldNames.uzon_steps: uzon_steps,
    }
