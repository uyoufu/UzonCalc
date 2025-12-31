from core.setup import get_current_instance
from core.renders.step_renderers import StepRenderer

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
    pass


def endline():
    pass


# endregion


# region renderer selection
def set_renderer(renderer: str | StepRenderer):
    """
    Update the step renderer for the current context.
    renderer can be a registered renderer name or an object implementing render(event).
    """

    ctx = get_current_instance()
    ctx.options.step_renderer = renderer


def use_text_renderer():
    set_renderer("text")


def use_latex_renderer():
    set_renderer("latex")


def use_html_renderer():
    set_renderer("html")


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
    ctx.aliases[name] = value

    return value


# endregion
