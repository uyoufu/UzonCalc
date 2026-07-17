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


# region enable/disable f-string equation rendering
def enable_fstring_equation():
    """启用 f-string 表达式的方程渲染。"""
    ctx = get_current_instance()
    ctx.options.enable_fstring_equation = True


def disable_fstring_equation():
    """禁用 f-string 表达式的方程渲染，仅显示表达式值。"""
    ctx = get_current_instance()
    ctx.options.enable_fstring_equation = False


# endregion


# region enable/disable formula expression rendering
def enable_formula_expression():
    """
    enable formula expression rendering
    """
    ctx = get_current_instance()
    ctx.options.enable_formula_expression = True


def disable_formula_expression():
    """
    disable formula expression rendering
    """
    ctx = get_current_instance()
    ctx.options.enable_formula_expression = False


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


def end_inline():
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


__all__ = [
    "alias",
    "decimal",
    "disable_formula_expression",
    "disable_fstring_equation",
    "disable_substitution",
    "enable_formula_expression",
    "enable_fstring_equation",
    "enable_substitution",
    "end_inline",
    "figure_prefix",
    "hide",
    "inline",
    "show",
    "table_prefix",
]
