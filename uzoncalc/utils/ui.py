from dataclasses import dataclass, asdict
import asyncio

from ..context import CalcContext
from ..setup import get_current_instance


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


async def UI(title: str, fields: list[Field], caption: str | None = None) -> dict:
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
        # 静默模式：直接返回默认值
        return {field.name: get_inputs(ctx, title, field) for field in fields}

    else:
        # 异步交互模式：返回 UI 定义供前端展示
        # 1. 更新 fields 的默认值
        for field in fields:
            field.default = get_inputs(ctx, title, field)

        # 2. 构造 UI 请求
        window = Window(title=title, fields=fields, caption=caption)
        ctx.interaction.required_ui = window

        # 3. 初始化并触发信号
        ctx.interaction.prepare_request()

        # 4. 等待用户输入
        # The runner will set the result of input_future with the user input dict
        try:
            input_data = await ctx.interaction.wait_for_input()
        except asyncio.CancelledError:
            raise

        # 5. 清理状态
        ctx.interaction.clear()

        # 6. 更新上下文并返回
        if input_data:
            if title not in ctx.vars:
                ctx.vars[title] = {}
            ctx.vars[title].update(input_data)

        # 返回结果
        return input_data
