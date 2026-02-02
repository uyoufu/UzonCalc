from __future__ import annotations
from dataclasses import dataclass, asdict
import asyncio
from typing import TYPE_CHECKING

from ..utils_core.dot_dict import DotDict, deep_update

if TYPE_CHECKING:
    from ..context import CalcContext
from ..globals import get_current_instance


class FieldType:
    text = "text"
    number = "number"
    selectOne = "selectOne"
    selectMany = "selectMany"
    checkbox = "checkbox"
    textarea = "textarea"


@dataclass(slots=True)
class Field:
    name: str
    label: str
    type: str = FieldType.text
    placeholder: str | None = None
    default: str | int | float | bool | None = None
    options: list[str] | None = None
    vif: str | None = None


# 请求变量输入的数据结构
@dataclass(slots=True)
class UIPayloads:
    windows: list[Window]  # 收集的所有 UI 定义
    html: str = ""
    is_waiting_for_input: bool = False  # 是否在等待用户输入


@dataclass(frozen=True, slots=True)
class Window:
    title: str
    fields: list[Field]
    caption: str | None = None


def get_inputs(ctx: CalcContext, name: str, field: Field):
    """从 ctx 中获取 UI 输入值"""
    vars = ctx.vars.get(name, {})
    if field.name in vars:
        return vars[field.name]
    return field.default


async def UI(title: str, fields: list[Field], caption: str | None = None) -> DotDict:
    """
    定义 UI
    Args:
        title: 窗口标题
        fields: 字段列表
        caption: 窗口底部说明文字
    Returns:
        返回 {field: value} 字典，key 为字段名，value 为用户输入的值
    """

    ctx = get_current_instance()

    # 判断执行模式
    if ctx.is_silent:
        # 静默模式：收集 UI 定义并返回默认值
        # 1. 更新 fields 的默认值
        for field in fields:
            field.default = get_inputs(ctx, title, field)

        # 2. 收集 Window 定义
        window = Window(title=title, fields=fields, caption=caption)
        ctx.ui_windows.append(window)

        # 3. 返回默认值
        return DotDict({field.name: get_inputs(ctx, title, field) for field in fields})

    else:
        # 异步交互模式：返回 UI 定义供前端展示
        # 1. 更新 fields 的默认值
        for field in fields:
            field.default = get_inputs(ctx, title, field)

        # 2. 生成信号
        ctx.interaction.set_input_feature()

        # 3. 返回结果
        window = Window(title=title, fields=fields, caption=caption)
        result = UIPayloads(
            html=ctx.html(),
            windows=[window],
            is_waiting_for_input=True,
        )
        ctx.interaction.set_result(result)

        # 4. 等待用户输入
        # The runner will set the result of input_future with the user input dict
        try:
            all_inputs = await ctx.interaction.wait_for_input()
        except asyncio.CancelledError:
            raise

        # 6. 更新上下文并返回
        if all_inputs:
            deep_update(ctx.vars, all_inputs)
        # 当不存在时，从 fields 中获取默认更新到 ctx.vars 中
        for field in fields:
            if title not in ctx.vars:
                ctx.vars[title] = {}
            ui_vars = ctx.vars[title]
            if field.name not in ui_vars:
                ui_vars[field.name] = field.default

        # 返回结果
        return DotDict(ctx.vars.get(title, {}))
