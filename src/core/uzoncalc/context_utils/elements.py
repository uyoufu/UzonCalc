from __future__ import annotations

import base64
from dataclasses import replace
import html
import inspect
import io
import re
from typing import Any, Iterable, List

from ..globals import get_current_instance
from .element_models import AutoLabel, HtmlFragment, ISavefig, LabelKind, Props
from .markdown import get_markdown


def create_auto_label(kind: LabelKind) -> AutoLabel:
    """按当前上下文配置创建自动编号标签。"""
    ctx = get_current_instance()
    serial_number = ctx.get_serial_number()
    prefix_settings = ctx.options.prefix_settings
    prefix = (
        prefix_settings.figure_prefix
        if kind is LabelKind.FIGURE
        else prefix_settings.table_prefix
    )
    return AutoLabel(kind=kind, label_id=f"{kind.value}-{serial_number}", prefix=prefix)


def props(**kwargs) -> Props:
    """
    Convenience function to create Props with custom attributes.

    Example:
        props(id="my-id", classes="foo bar", data_value="123", aria_label="Label")

    :param kwargs: Keyword arguments for Props attributes.
    :return: Props instance.
    """
    # Extract known attributes
    classes = kwargs.pop("classes", None)
    styles = kwargs.pop("styles", None)
    id_attr = kwargs.pop("id", None)

    # Remaining kwargs become custom attributes
    return Props(class_str=classes, style=styles, id=id_attr, custom=kwargs)


def h(
    tag: str,
    children: str | List[str] | None = None,
    classes: str | None = None,
    *,
    props: Props | None = None,
    persist: bool = False,
    is_self_closing: bool = False,
) -> str:
    """
    Create an HTML string representation.

    :param tag: The HTML tag name (e.g., 'div', 'span').
    :param children: A string or a list of child elements.
    :param classes: CSS classes to apply (overrides props.classes).
    :param props: Props instance with HTML attributes.
    :param persist: If True, append to the current document context.
    :return: A string representing the HTML.
    """
    element_props = _merge_classes(props, classes)
    props_str = _props_to_html(element_props)
    children_str = _children_to_html(children)

    if is_self_closing:
        html_result = f"<{tag}{props_str} />"
    else:
        html_result = f"<{tag}{props_str}>{children_str}</{tag}>"

    if persist:
        get_current_instance().append_content(html_result)
    return html_result


def title(text: str, classes: str | None = None, *, persist: bool = False):
    """
    设置文档标题
    :param text: 标题文本
    """
    default_props = Props(class_str="font-bold text-4xl text-center my-4")
    return h("p", text, classes=classes, props=default_props, persist=persist)


def Title(text: str, classes: str | None = None):
    """
    设置文档标题
    :param text: 标题文本
    """
    title(text, classes=classes, persist=True)


def subtitle(text: str, classes: str | None = None, *, persist: bool = False):
    """
    设置文档副标题
    :param text: 副标题文本
    """
    default_props = Props(class_str="font-bold text-center")
    return h("p", text, classes=classes, props=default_props, persist=persist)


def Subtitle(text: str, classes: str | None = None):
    """
    设置文档副标题
    :param text: 副标题文本
    """
    subtitle(text, classes=classes, persist=True)


def H(content: str | List[str], *, props: Props | None = None):
    """
    render a level 0 heading
    :param content: heading content
    """
    h("h0", children=content, props=props, persist=True)


def h1(
    content: str | List[str],
    classes: str | None = None,
    *,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    """
    render a level 1 heading
    :param content: heading content
    :param classes: CSS classes to apply (overrides props.classes)
    """
    return h("h1", content, classes=classes, props=props, persist=persist)


def H1(
    content: str | List[str], classes: str | None = None, *, props: Props | None = None
):
    """
    render a level 1 heading
    :param content: heading content
    """
    h1(content, classes=classes, props=props, persist=True)


def h2(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    return h("h2", content, classes=classes, props=props, persist=persist)


def H2(content: str | List[str], *, props: Props | None = None):
    h2(content, props=props, persist=True)


def h3(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    return h("h3", content, classes=classes, props=props, persist=persist)


def H3(content: str | List[str], *, props: Props | None = None):
    h3(content, props=props, persist=True)


def h4(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    return h("h4", content, classes=classes, props=props, persist=persist)


def H4(content: str | List[str], *, props: Props | None = None):
    h4(content, props=props, persist=True)


def h5(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    return h("h5", content, classes=classes, props=props, persist=persist)


def H5(content: str | List[str], *, props: Props | None = None):
    h5(content, props=props, persist=True)


def h6(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    return h("h6", content, classes=classes, props=props, persist=persist)


def H6(content: str | List[str], *, props: Props | None = None):
    h6(content, props=props, persist=True)


def p(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    return h("p", content, classes=classes, props=props, persist=persist)


def P(
    content: str | List[str], *, classes: str | None = None, props: Props | None = None
):
    p(content, classes=classes, props=props, persist=True)


def div(
    content: str | List[str],
    classes: str | None = None,
    *,
    props: Props | None = None,
    persist: bool = False,
):
    return h("div", content, classes=classes, props=props, persist=persist)


def Div(
    content: str | List[str],
    classes: str | None = None,
    *,
    props: Props | None = None,
):
    div(content, classes=classes, props=props, persist=True)


def span(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
):
    return h("span", content, classes=classes, props=props, persist=persist)


def Span(content: str | List[str], *, props: Props | None = None):
    span(content, props=props, persist=True)


def br():
    return h("br", persist=False, is_self_closing=True)


def Br():
    h("br", persist=True, is_self_closing=True)


def row(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
    tag: str = "div",
):
    return h(tag, content, classes=classes, props=props, persist=persist)


def Row(content: str | List[str], *, props: Props | None = None, tag: str = "div"):
    row(content, props=props, tag=tag, persist=True)


def img(
    src: str,
    classes: str | None = None,
    *,
    alt: str | None = None,
    width: str | int | None = None,
    height: str | int | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    attrs = {"src": src, "alt": alt, "width": width, "height": height}
    img_props = _extend_props(props, attrs)
    children = [h("img", classes=classes, props=img_props, is_self_closing=True)]
    if alt:
        children.append(div(alt))
    result = div(children, classes="flex flex-col items-center justify-center")
    if persist:
        get_current_instance().append_content(result)
    return result


def Img(
    src: str,
    classes: str | None = None,
    *,
    alt: str | None = None,
    width: str | int | None = None,
    height: str | int | None = None,
    props: Props | None = None,
):
    label = create_auto_label(LabelKind.FIGURE)
    caption_children: list[str] = [str(label.source_html())]
    if alt:
        caption_children.append(alt)
    img_props = _extend_props(
        props, {"src": src, "alt": alt, "width": width, "height": height}
    )
    image_html = h("img", classes=classes, props=img_props, is_self_closing=True)
    h(
        "figure",
        [
            div(image_html, classes="uzoncalc-figure-body"),
            h(
                "figcaption",
                caption_children,
                classes="uzoncalc-label-caption uzoncalc-label-caption-figure",
            ),
        ],
        classes="uzoncalc-figure-wrapper",
        persist=True,
    )
    return label.reference_html()


def input(content: str, persist: bool = False):
    return h("input", props=Props(custom={"value": content}), persist=persist)


def Input(content: str):
    input(content, persist=True)


def code(content: str, language: str | None = None, persist: bool = False):
    cleaned_content = inspect.cleandoc(content)
    lang_class = f"language-{language}" if language else ""
    code_html = h("code", children=cleaned_content, classes=lang_class)
    return h("pre", children=code_html, classes="my-2 ml-8", persist=persist)


def Code(content: str, language: str | None = None):
    code(content, language=language, persist=True)


def info(content: str, persist: bool = False):
    classes = (
        "flex flex-row items-center bg-blue-100 "
        "text-blue-500 px-4 py-3 rounded relative"
    )
    return div(content, classes=classes, persist=persist)


def Info(content: str):
    info(content, persist=True)


def markdown(content: str, persist: bool = False):
    """
    render markdown content
    :param content: markdown content
    :param trim: whether to trim start and end of content
    :return: html content
    """
    md = get_markdown()

    # 移除 content 开头的空行（含仅空白字符的行）
    cleaned_content = inspect.cleandoc(content)
    markdown_html = md.render(cleaned_content)
    # 不能直接使用 p 标签，因为 p 标签中无法包含列表等元素
    return div(markdown_html, persist=persist)


def Markdown(content: str):
    markdown(content, persist=True)


def laTex(content: str, persist: bool = False):
    """渲染块级 LaTeX 公式，交由 HTML 模板中的 KaTeX 运行时排版。"""
    return h("latex", children=html.escape(content), classes="latex", persist=persist)


def LaTex(content: str):
    laTex(content, persist=True)


def plot(fig: ISavefig, width=None, persist: bool = False):
    """
    将 Matplotlib 图形渲染为内嵌 PNG 图片。
    """
    image_base64 = base64.b64encode(_save_plot_to_bytes(fig)).decode("ascii")
    return img(f"data:image/png;base64,{image_base64}", width=width, persist=persist)


def Plot(
    fig: ISavefig | bytes | bytearray | memoryview,
    *,
    width=None,
    caption: str = "",
):
    """
    将 Matplotlib 图形或 PNG 二进制内容追加到当前文档。
    """
    if isinstance(fig, (bytes, bytearray, memoryview)):
        # 二进制内容直接编码为 data URL，避免误传给 Figure 渲染逻辑。
        image_base64 = base64.b64encode(fig).decode("ascii")
        return Img(f"data:image/png;base64,{image_base64}", width=width)
    image_base64 = base64.b64encode(_save_plot_to_bytes(fig)).decode("ascii")
    return Img(
        f"data:image/png;base64,{image_base64}",
        width=width,
        alt=caption,
    )


def _save_plot_to_bytes(fig: ISavefig) -> bytes:
    """将 Matplotlib 图形保存为 PNG 二进制内容。"""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()


def _merge_classes(element_props: Props | None, classes: str | None) -> Props | None:
    if classes is None:
        return element_props
    if element_props is None:
        return Props(class_str=classes)
    return replace(element_props, class_str=classes)


def _extend_props(element_props: Props | None, attrs: dict[str, Any]) -> Props:
    base = element_props or Props()
    custom = dict(base.custom)
    for key, value in attrs.items():
        if value is not None:
            custom[key] = value
    return replace(base, custom=custom)


def _props_to_html(element_props: Props | None) -> str:
    if element_props is None:
        return ""
    return element_props.to_html_attrs()


def _children_to_html(children: str | List[str] | None) -> str:
    if children is None:
        return ""
    if isinstance(children, list):
        return "".join(str(child) for child in children)
    return str(children)
