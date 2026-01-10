from typing import Any
from core.setup import get_current_instance

# region show/hide content recording


def show():
    """
    set is_skip_content false, enable content recording
    """

    ctx = get_current_instance()
    ctx.options.skip_content = False


def hide():
    """
    set is_skip_content true, skip content recording
    """

    ctx = get_current_instance()
    ctx.options.skip_content = True


# endregion


# region enable/disable variable substitution in equations
def enable_substitution():
    """
    enable variable substitution in equations
    """
    ctx = get_current_instance()
    ctx.options.enable_substitution = True


def disable_substitution():
    """
    disable variable substitution in equations
    """
    ctx = get_current_instance()
    ctx.options.enable_substitution = False


# endregion


# region inline
def inline():
    ctx = get_current_instance()
    ctx.start_inline()


def endline():
    ctx = get_current_instance()
    ctx.end_inline()


# endregion


# region define variable symbols
def alias(name, value):
    """
    define a variable symbol
    :param name: variable name
    :param value: variable value
    """
    ctx = get_current_instance()
    # 将别名保存到上下文的别名字典中
    ctx.options.aliases[name] = value

    return value


# endregion


# region 页面设置
def doc_title(title: str):
    """
    设置页面标题
    :param title: 页面标题
    """
    ctx = get_current_instance()
    ctx.options.page_title = title


def page_size(size: str):
    """
    设置页面大小
    :param size: 页面大小，如 'A4', 'Letter' 等
    """
    ctx = get_current_instance()
    ctx.options.page_size = size


def style(name: str, value: dict[str, Any]):
    """
    设置页面样式
    :param name: 样式名称
    :param value: 样式内容，字典形式
    """
    ctx = get_current_instance()
    ctx.options.styles[name] = dict(value)


# endregion
