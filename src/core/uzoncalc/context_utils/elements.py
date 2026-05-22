from __future__ import annotations

import base64
from dataclasses import dataclass, field, replace
import html
import io
from typing import Any, Iterable, List, Protocol

from ..globals import get_current_instance


class ISavefig(Protocol):
    """
    支持保存为图片的 Matplotlib 绘图对象协议。
    """

    def savefig(self, *args: Any, **kwargs: Any) -> Any:
        """
        保存当前绘图内容到目标缓冲区或文件。
        """
        ...


@dataclass
class Props:
    """
    HTML element properties class.

    Supports standard HTML attributes and custom attributes.

    Example:
        Props(id="my-id", classes="foo bar", styles={"color": "red"})
        Props(id="my-id", data_value="123")
    """

    class_str: str | None = None
    style: dict[str, str] | None = None
    id: str | None = None
    custom: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, str]:
        """
        Convert Props to a dictionary of HTML attributes.

        :return: Dictionary mapping attribute names to their string values.
        """
        attrs: dict[str, str] = {}

        # Handle id
        if self.id:
            attrs["id"] = self.id

        # Handle classes
        if self.class_str:
            attrs["class"] = self.class_str

        # Handle styles
        if self.style:
            attrs["style"] = "; ".join(f"{k}: {v}" for k, v in self.style.items())

        # Handle custom attributes
        for key, value in self.custom.items():
            if value is not None:
                # Convert underscores to hyphens for HTML attributes
                # e.g. data_value -> data-value
                attrs[key.replace("_", "-")] = str(value)
        return attrs


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


def P(content: str | List[str], *, props: Props | None = None):
    p(content, props=props, persist=True)


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
    img(
        src,
        classes=classes,
        alt=alt,
        width=width,
        height=height,
        props=props,
        persist=True,
    )


def input(content: str, persist: bool = False):
    return h("input", props=Props(custom={"value": content}), persist=persist)


def Input(content: str):
    input(content, persist=True)


def code(content: str, language: str | None = None):
    lines = _trim_empty_lines(content.split("\n"))
    lang_class = f"language-{language}" if language else ""
    code_html = h("code", children="\n".join(lines), classes=lang_class)
    return h("pre", children=code_html, classes="my-2")


def Code(content: str, language: str | None = None):
    get_current_instance().append_content(code(content, language=language))


def info(content: str, persist: bool = False):
    classes = (
        "flex flex-row items-center bg-blue-100 border border-blue-400 "
        "text-blue-700 px-4 py-3 rounded relative"
    )
    return div(content, classes=classes, persist=persist)


def Info(content: str):
    info(content, persist=True)


def laTex(content: str, persist: bool = False):
    return h("latex", children=content, persist=persist)


def LaTex(content: str):
    laTex(content, persist=True)


def plot(fig: ISavefig, width=None, persist: bool = False):
    """
    将 Matplotlib 图形渲染为内嵌 PNG 图片。
    """
    # 通过内存缓冲区导出图片，避免生成临时文件。
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return img(f"data:image/png;base64,{image_base64}", width=width, persist=persist)


def Plot(fig: ISavefig | bytes | bytearray | memoryview, width=None):
    """
    将 Matplotlib 图形或 PNG 二进制内容追加到当前文档。
    """
    if isinstance(fig, (bytes, bytearray, memoryview)):
        # 二进制内容直接编码为 data URL，避免误传给 Figure 渲染逻辑。
        image_base64 = base64.b64encode(fig).decode("ascii")
        Img(f"data:image/png;base64,{image_base64}", width=width)
        return
    plot(fig, width=width, persist=True)


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
    attrs = element_props.to_dict()
    if not attrs:
        return ""
    attr_text = " ".join(
        f'{key}="{html.escape(value, quote=True)}"' for key, value in attrs.items()
    )
    return f" {attr_text}"


def _children_to_html(children: str | List[str] | None) -> str:
    if children is None:
        return ""
    if isinstance(children, list):
        return "".join(str(child) for child in children)
    return str(children)


def _trim_empty_lines(lines: Iterable[str]) -> list[str]:
    trimmed = list(lines)
    while trimmed and trimmed[0].strip() == "":
        trimmed.pop(0)
    while trimmed and trimmed[-1].strip() == "":
        trimmed.pop()
    return trimmed
