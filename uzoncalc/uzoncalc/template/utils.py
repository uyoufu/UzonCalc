"""
HTML template for rendering calculation sheets with LaTeX support.
"""

import html
import os
from typing import Any
from ..context_options import ContextOptions

# 模板缓存，避免重复加载文件
_template_cache: str | None = None


def load_template() -> str:
    """
    从模板文件中加载 HTML 模板（带缓存）

    Returns:
        HTML 模板字符串
    """
    global _template_cache

    if _template_cache is None:
        template_dir = os.path.join(os.path.dirname(__file__))
        template_file = os.path.join(template_dir, "calc_template.html")

        with open(template_file, "r", encoding="utf-8") as f:
            _template_cache = f.read()

    return _template_cache


def generate_custom_styles(styles: dict[str, dict[str, Any]]) -> str:
    """
    根据用户自定义样式字典生成 CSS 样式字符串

    Args:
        styles: 样式字典，格式为 {选择器: {属性: 值}}

    Returns:
        CSS 样式字符串
    """
    if not styles:
        return ""

    css_lines = []
    for selector, properties in styles.items():
        css_lines.append(f"{selector} {{")
        for prop, value in properties.items():
            # 将 Python 风格的属性名转换为 CSS 风格
            # 例如: font_size -> font-size
            css_prop = prop.replace("_", "-")
            css_lines.append(f"    {css_prop}: {value};")
        css_lines.append("}")

    return "\n".join(css_lines)


def generate_custom_heads(heads: dict[str, tuple[str, dict[str, str]]]) -> str:
    """
    根据用户自定义头部字典生成 HTML 头部标签字符串

    Args:
        heads: 头部字典，格式为 {内容 hash: (标签名, {属性名: 属性值})}

    Returns:
        HTML 头部标签字符串
    """
    if not heads:
        return ""

    void_tags = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    head_lines = []
    for _, (tag, attrs) in heads.items():
        if not tag:
            continue

        attr_parts = []
        for attr_name, attr_value in attrs.items():
            if attr_value is None:
                continue

            attr_parts.append(
                f'{attr_name}="{html.escape(str(attr_value), quote=True)}"'
            )

        attr_text = f" {' '.join(attr_parts)}" if attr_parts else ""
        if tag.lower() in void_tags:
            head_lines.append(f"<{tag}{attr_text}>")
        else:
            head_lines.append(f"<{tag}{attr_text}></{tag}>")

    return "\n".join(head_lines)


def render_html_template(content: str, options: ContextOptions) -> str:
    """
    使用模板和选项生成最终的 HTML 内容

    Args:
        content: 主要内容
        options: 上下文选项,包含页面标题、尺寸、自定义样式等

    Returns:
        完整的 HTML 字符串
    """
    # 加载模板（使用缓存）
    template = load_template()

    # 获取页面尺寸
    page_size, page_width = options.page_info.get_page_size_dimensions()

    # 生成自定义头部内容
    custom_heads = generate_custom_heads(options.heads)

    # 生成自定义样式
    custom_styles = generate_custom_styles(options.styles)

    # 一次性替换所有占位符，避免多次字符串复制
    replacements = {
        "BODY_FONT_FAMILY": options.page_info.font_family,
        "PAGE_TITLE": options.doc_title,
        "PAGE_SIZE": page_size,
        "PAGE_WIDTH": page_width,
        "CUSTOM_STYLES": custom_styles,
        "CUSTOM_HEADS": custom_heads,
        "PAGE_MARGIN": options.page_info.margin,
        "CONTENT": content,
    }

    html_output = template
    for placeholder, value in replacements.items():
        html_output = html_output.replace(placeholder, value)

    return html_output


def get_html_template(content: str) -> str:
    """
    Generate HTML template with user-provided content and LaTeX rendering support.

    此函数保留用于向后兼容，推荐使用 render_html_template

    Args:
        content: The main content to be inserted into the template.

    Returns:
        Complete HTML string.
    """
    from ..context_options import ContextOptions

    default_options = ContextOptions()
    return render_html_template(content, default_options)
