from typing import Any
from ..setup import get_current_instance


def doc_title(title: str):
    """
    设置页面标题
    :param title: 页面标题
    """
    ctx = get_current_instance()
    ctx.options.doc_title = title


def font_family(family: str):
    """
    设置页面字体
    :param family: 字体名称，如 'Arial', 'Times New Roman' 等
    """
    ctx = get_current_instance()
    ctx.options.page_info.font_family = family


def page_size(size: str):
    """
    设置页面大小
    :param size: 页面大小，如 'A4', 'Letter' 等
    """
    ctx = get_current_instance()
    ctx.options.page_info.size = size


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
    from ..template.utils import render_html_template
    import shutil
    import os
    import inspect

    ctx = get_current_instance()

    if not filename:
        # 以当前的标题作为文件名
        filename = ctx.options.doc_title or "UzonCalc Sheet"

    # 没有扩展名则添加 .html
    if not filename.endswith(".html"):
        filename += ".html"

    # 如果 filename 不是绝对路径，则保存到调用者文件所在的目录
    if not os.path.isabs(filename):
        caller_dir = ctx.get_location_dir()
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
        print(f"Warning: Unable to copy CSS file: {e}")

    # Show web url
    print(f"Document saved to (open with browser): file:///{filename}")


def toc(title: str = "Table of Contents"):
    """
    插入目录
    :param title: 目录标题
    """
    ctx = get_current_instance()
    # 在当前位置插入目录占位符，JavaScript 会自动填充内容
    toc_html = f"""
<div id='toc' style='page-break-before:always;page-break-after:always;'>
    <div class='text-center text-2xl font-semibold'>{title}</div>
    <div id='toc-container'></div>
</div>
"""
    ctx.append_content(toc_html)
