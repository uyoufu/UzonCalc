from dataclasses import dataclass, asdict
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


async def UI(title: str, fields: list[Field], caption: str | None = None) -> dict:
    """创建 UI 窗口定义"""
    window = Window(title=title, fields=fields)
    # 设置初始值
    ctx = get_current_instance()

    # 从上下文中获取已有值
    return asdict(window)
