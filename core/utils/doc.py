# region 页面设置
from typing import Any
from core.setup import get_current_instance


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


def save(filename: str | None = None):
    """
    保存当前文档为指定文件
    :param filename: 文件名（可以是完整路径或仅文件名）
    """
    from core.template.utils import render_html_template
    import shutil
    import os
    import inspect

    ctx = get_current_instance()

    if not filename:
        # 以当前的标题作为文件名
        filename = ctx.options.page_title or "UzonCalc Sheet"

    # 没有扩展名则添加 .html
    if not filename.endswith(".html"):
        filename += ".html"

    # 如果 filename 不是绝对路径，则保存到调用者文件所在的目录
    if not os.path.isabs(filename):
        # 获取调用者的文件路径
        frame = inspect.stack()[1]
        caller_file = frame.filename
        caller_dir = os.path.dirname(os.path.abspath(caller_file))
        filename = os.path.join(caller_dir, filename)

    # 获取内容
    content = ctx.html_content()

    # 使用模板渲染 HTML
    html_output = render_html_template(content, ctx.options)

    # 保存为 HTML 文件
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_output)

    # 复制 CSS 文件到同一目录
    output_dir = os.path.dirname(os.path.abspath(filename))
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "template")
    css_source = os.path.join(template_dir, "template.css")
    css_dest = os.path.join(output_dir, "template.css")

    try:
        shutil.copy2(css_source, css_dest)
    except Exception as e:
        print(f"警告：无法复制 CSS 文件: {e}")


# endregion
