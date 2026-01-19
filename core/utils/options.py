from typing import Any
from ..setup import get_current_instance

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


# region fstring equation
def enable_fstring_equation():
    """
    enable fstring equation rendering
    """
    ctx = get_current_instance()
    ctx.options.enable_fstring_equation = True


def disable_fstring_equation():
    """
    disable fstring equation rendering
    """
    ctx = get_current_instance()
    ctx.options.enable_fstring_equation = False


# endregion


# region inline
def inline(separator: str = " "):
    ctx = get_current_instance()
    ctx.start_inline(separator)


def endline():
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
