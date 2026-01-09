import ast
import inspect
import textwrap
import threading
from types import FunctionType
from typing import Any, Callable, Dict
import weakref

from core.handcalc.ast_visitor import AstNodeVisitor
from core.handcalc.field_names import FieldNames

# 按“原函数对象”缓存插桩结果，确保同一函数只插桩一次（并发安全）
_instrument_cache: "weakref.WeakKeyDictionary[Callable[..., Any], FunctionType]" = (
    weakref.WeakKeyDictionary()
)
_instrument_lock = threading.Lock()


def instrument_function(func: Callable[..., Any]) -> FunctionType:
    """
    返回插桩后的函数。

    说明：插桩后的代码会在记录步骤时引用变量名 `ctx`。
    为了让被装饰函数即使不显式声明 `ctx` 形参也能正常运行，
    本函数会在函数体顶部自动注入：

        ctx = get_current_instance()
    """
    # 如果传进来的本身就是插桩后的函数，直接返回
    if getattr(func, FieldNames.uzon_instrumented, False):
        return func  # type: ignore[return-value]

    # 并发/重复调用：同一个原函数对象只插桩一次
    with _instrument_lock:
        cached = _instrument_cache.get(func)
        if cached is not None:
            return cached

        # 获取源码并去除非必要缩进
        src = textwrap.dedent(inspect.getsource(func))
        mod = ast.parse(src)

        def _function_has_param(
            node: ast.FunctionDef | ast.AsyncFunctionDef, name: str
        ) -> bool:
            args = node.args
            return any(
                a.arg == name
                for a in (
                    list(args.posonlyargs)
                    + list(args.args)
                    + list(args.kwonlyargs)
                    + ([args.vararg] if args.vararg else [])
                    + ([args.kwarg] if args.kwarg else [])
                )
            )

        def _inject_ctx_acquire(node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            # If user already declares ctx, don't override it.
            if _function_has_param(node, FieldNames.ctx):
                return

            assign_ctx = ast.Assign(
                targets=[ast.Name(id=FieldNames.ctx, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id=FieldNames.get_current_instance, ctx=ast.Load()),
                    args=[],
                    keywords=[],
                ),
            )

            # 将 get_current_instance 标记为跳过记录，避免被处理器修改
            setattr(assign_ctx, FieldNames.skip_record, True)

            # Preserve docstring position: insert after it when present.
            insert_at = 0
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(
                    getattr(node.body[0], FieldNames.value, None), ast.Constant
                )
                and isinstance(
                    getattr(node.body[0].value, FieldNames.value, None), str
                )
            ):
                insert_at = 1
            node.body.insert(insert_at, assign_ctx)

        # 关键：inspect.getsource 会包含原函数装饰器（如 @uzon_calc()）。
        # 如果不移除，exec 编译后的代码会再次应用装饰器，导致 wrapper 套娃递归，
        # 从而出现 “sheet() takes 2 positional arguments but N were given”。
        for node in mod.body:
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == func.__name__
            ):
                node.decorator_list = []
                _inject_ctx_acquire(node)
                break

        # 调用所有的 visitor 进行处理
        ast_visitor = AstNodeVisitor()
        mod = ast_visitor.visit(mod)

        # 编译前的“补位”,确保 AST 节点信息完整
        ast.fix_missing_locations(mod)
        # 编译插桩后的代码
        code = compile(
            mod, filename=inspect.getsourcefile(func) or "<instrumented>", mode="exec"
        )

        glb: Dict[str, Any] = dict(func.__globals__)
        # 注入记录步骤的函数
        from core.handcalc import record_step

        glb[FieldNames.uzon_record_step] = record_step.record_step

        # 注入 get_current_instance，供插桩后函数体使用。
        # 采用运行时导入避免模块导入阶段的循环依赖。
        from core.setup import get_current_instance

        glb[FieldNames.get_current_instance] = get_current_instance

        # Inject v2 IR module for building MathNode dataclasses at runtime.
        from core.handcalc.v2 import ir as uzon_ir

        glb[FieldNames.uzon_ir] = uzon_ir

        # Inject Step classes module for building Step objects at runtime.
        from core.handcalc import steps as uzon_steps

        glb[FieldNames.uzon_steps] = uzon_steps

        loc: Dict[str, Any] = {}
        # 真正执行编译后的代码：这一步会运行模块级语句，通常会把被插桩后的函数定义放进 loc
        exec(code, glb, loc)

        new_func = loc.get(func.__name__)
        if not isinstance(new_func, FunctionType):
            raise RuntimeError("instrument_function: failed to rebuild function")

        # 打标记：避免对“插桩后的函数”重复插桩
        try:
            setattr(new_func, FieldNames.uzon_instrumented, True)
        except Exception:
            pass

        # 缓存并返回
        _instrument_cache[func] = new_func
        return new_func
