from typing import Any
from ..globals import get_current_instance

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


# disable/enable equation rendering
def disable_equation():
    """
    disable equation rendering
    """
    pass


def enable_equation():
    """
    enable equation rendering
    """
    pass


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
def inline(separator: str = " "):
    ctx = get_current_instance()
    ctx.start_inline(separator)


def endInline():
    ctx = get_current_instance()
    ctx.end_inline()


# endregion


# region define variable symbols
def alias(name, value):
    """
    define a variable symbol
    :param name: variable name
    :param value: variable value, None to remove alias
    """
    if not name:
        return
    ctx = get_current_instance()
    # 将别名保存到上下文的别名字典中
    ctx.options.aliases[name] = value


# endregion


# region decimal precision
def decimal(float_precision: int):
    """
    set float display precision in decimal places
    :param float_precision: number of decimal places to display, default is 3
    """
    ctx = get_current_instance()
    ctx.options.float_precision = float_precision


# endregion


# region figure/table prefix
def figure_prefix(prefix: str = "Figure"):
    """
    set figure prefix
    :param prefix: figure prefix, default is "Figure"
    """
    ctx = get_current_instance()
    ctx.options.prefix_settings.figure_prefix = prefix


def table_prefix(prefix: str = "Table"):
    """
    set table prefix
    :param prefix: table prefix, default is "Table"
    """
    ctx = get_current_instance()
    ctx.options.prefix_settings.table_prefix = prefix


# endregion
