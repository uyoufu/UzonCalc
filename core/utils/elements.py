import base64
from dataclasses import dataclass, field
import io
from typing import Any, List

from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from ..setup import get_current_instance


# region Data Classes
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

    def __post_init__(self):
        """Process any additional keyword arguments as custom attributes."""
        pass

    def to_dict(self) -> dict[str, str]:
        """
        Convert Props to a dictionary of HTML attributes.

        :return: Dictionary mapping attribute names to their string values.
        """
        attrs = {}

        # Handle id
        if self.id:
            attrs["id"] = self.id

        # Handle classes
        if self.class_str:
            attrs["class"] = self.class_str

        # Handle styles
        if self.style:
            style_str = "; ".join(f"{k}: {v}" for k, v in self.style.items())
            attrs["style"] = style_str

        # Handle custom attributes
        if self.custom:
            for key, value in self.custom.items():
                # Convert underscores to hyphens for HTML attributes (e.g., data_value -> data-value)
                html_key = key.replace("_", "-")
                attrs[html_key] = str(value)

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


# endregion


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
    :param persist: If True, will append to the current document context.
    :return: A string representing the HTML.
    """
    children = children or []

    # Handle classes override
    if classes is not None:
        if props is None:
            props = Props(class_str=classes)
        else:
            props = Props(
                class_str=classes, style=props.style, id=props.id, custom=props.custom
            )

    # Convert Props to HTML attributes
    if props:
        attrs = props.to_dict()
        props_str = " ".join(f'{key}="{value}"' for key, value in attrs.items())
        props_str = f" {props_str}" if props_str else ""
    else:
        props_str = ""

    # Handle children
    if isinstance(children, list):
        children_str = "".join(children)
    else:
        children_str = children if children else ""

    # the HTML string
    if is_self_closing:
        html_result = f"<{tag}{props_str} />"
    else:
        html_result = f"<{tag}{props_str}>{children_str}</{tag}>"

    if persist:
        ctx = get_current_instance()
        ctx.append_content(html_result)

    return html_result


def H(content: str | List[str], *, props: Props | None = None):
    """
    render a level 0 heading
    :param content: heading content
    """
    h(
        "h0",
        children=content,
        props=props,
        persist=True,
    )


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
    return h(
        "h1",
        children=content,
        classes=classes,
        props=props,
        persist=persist,
    )


def H1(
    content: str | List[str], classes: str | None = None, *, props: Props | None = None
):
    """
    render a level 1 heading
    :param content: heading content
    """
    h1(
        content,
        classes=classes,
        props=props,
        persist=True,
    )


def h2(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    """
    render a level 2 heading
    :param content: heading content
    :param classes: CSS classes to apply (overrides props.classes)
    """
    return h(
        "h2",
        children=content,
        classes=classes,
        props=props,
        persist=persist,
    )


def H2(content: str | List[str], *, props: Props | None = None):
    """
    render a level 2 heading
    :param content: heading content
    """
    h2(
        content,
        props=props,
        persist=True,
    )


def h3(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    """
    render a level 3 heading
    :param content: heading content
    :param classes: CSS classes to apply (overrides props.classes)
    """
    return h(
        "h3",
        children=content,
        classes=classes,
        props=props,
        persist=persist,
    )


def H3(content: str | List[str], *, props: Props | None = None):
    """
    render a level 3 heading
    :param content: heading content
    """
    h3(
        content,
        props=props,
        persist=True,
    )


def h4(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    """
    render a level 4 heading
    :param content: heading content
    :param classes: CSS classes to apply (overrides props.classes)
    """
    return h(
        "h4",
        children=content,
        classes=classes,
        props=props,
        persist=persist,
    )


def H4(content: str | List[str], *, props: Props | None = None):
    """
    render a level 4 heading
    :param content: heading content
    """
    h4(
        content,
        props=props,
        persist=True,
    )


def h5(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    """
    render a level 5 heading
    :param content: heading content
    :param classes: CSS classes to apply (overrides props.classes)
    """
    return h(
        "h5",
        children=content,
        classes=classes,
        props=props,
        persist=persist,
    )


def H5(content: str | List[str], *, props: Props | None = None):
    """
    render a level 5 heading
    :param content: heading content
    """
    h5(
        content,
        props=props,
        persist=True,
    )


def h6(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    """
    render a level 6 heading
    :param content: heading content
    :param classes: CSS classes to apply (overrides props.classes)
    """
    return h(
        "h6",
        children=content,
        classes=classes,
        props=props,
        persist=persist,
    )


def H6(content: str | List[str], *, props: Props | None = None):
    """
    render a level 6 heading
    :param content: heading content
    """
    h6(
        content,
        props=props,
        persist=True,
    )


def p(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    """
    render a paragraph
    :param content: paragraph content
    :param classes: CSS classes to apply (overrides props.classes)
    """
    return h("p", children=content, classes=classes, props=props, persist=persist)


def P(content: str | List[str], *, props: Props | None = None):
    """
    render a paragraph
    :param content: paragraph content
    """
    p(content, props=props, persist=True)


def div(
    content: str | List[str],
    classes: str | None = None,
    *,
    props: Props | None = None,
    persist: bool = False,
):
    """
    render a div
    :param content: div content
    :param classes: CSS classes to apply (overrides props.classes)
    """
    return h("div", children=content, classes=classes, props=props, persist=persist)


def Div(
    content: str | List[str],
    classes: str | None = None,
    *,
    props: Props | None = None,
):
    h("div", children=content, classes=classes, props=props, persist=True)


def span(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
):
    """
    render a span
    :param content: span content
    :param classes: CSS classes to apply (overrides props.classes)
    """
    return h("span", children=content, classes=classes, props=props, persist=persist)


def Span(content: str | List[str], *, props: Props | None = None):
    """
    render a span
    :param content: span content
    """
    span(content, props=props, persist=True)


def br():
    """
    render a line break
    """
    return h("br", persist=False, is_self_closing=True)


def Br():
    """
    render a line break
    """
    h("br", persist=True, is_self_closing=True)


def row(
    content: str | List[str],
    *,
    classes: str | None = None,
    props: Props | None = None,
    persist: bool = False,
    tag: str = "div",
):
    """
    render a row
    :param content: row content
    :param classes: CSS classes to apply (overrides props.classes)
    """
    return h(tag, children=content, classes=classes, props=props, persist=persist)


def Row(
    content: str | List[str],
    *,
    props: Props | None = None,
    tag: str = "div",
):
    h(tag, children=content, props=props, persist=True)


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
    """
    render an image
    :param src: image source URL
    :param alt: alternative text for the image
    :param width: image width (in pixels or CSS units)
    :param height: image height (in pixels or CSS units)
    :param classes: CSS classes to apply (overrides props.classes)
    """
    custom_attrs = {"src": src}
    if alt is not None:
        custom_attrs["alt"] = alt
    if width is not None:
        custom_attrs["width"] = str(width)
    if height is not None:
        custom_attrs["height"] = str(height)

    if props is None:
        img_props = Props(custom=custom_attrs)
    else:
        img_props = Props(
            class_str=props.class_str,
            style=props.style,
            id=props.id,
            custom={**props.custom, **custom_attrs},
        )

    div_children = [
        h(
            "img",
            classes=classes,
            props=img_props,
            is_self_closing=True,
        )
    ]
    if alt:
        div_children.append(
            div(
                alt,
            )
        )
    result = div(
        div_children,
        classes="flex flex-col items-center justify-center",
    )

    if persist:
        ctx = get_current_instance()
        ctx.append_content(result)
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
    """
    render an image
    :param src: image source URL
    :param alt: alternative text for the image
    :param width: image width (in pixels or CSS units)
    :param height: image height (in pixels or CSS units)
    :param classes: CSS classes to apply (overrides props.classes)
    """
    img(
        src,
        alt=alt,
        width=width,
        height=height,
        classes=classes,
        props=props,
        persist=True,
    )


def table(
    headers: list[list[str | float]] | list[str | float],
    rows: list[list[str | float]] | list[str | float],
    classes: str | None = None,
    *,
    title: str | None = None,
    props: Props | None = None,
    persist: bool = False,
):
    """
    Render an HTML table.

    - headers: either a list of header strings (one header row) or a list of header rows (list of list).
    - rows: either a list of cell strings (one body row) or a list of body rows (list of list).
    - title: optional caption for the table.
    """
    # Normalize headers
    header_rows: list[list[str]] = []
    if headers:
        if isinstance(headers, list) and headers and isinstance(headers[0], list):
            header_rows = headers  # type: ignore
        elif isinstance(headers, list):
            header_rows = [headers]  # type: ignore

    # Normalize rows
    body_rows: list[list[str]] = []
    if rows:
        if isinstance(rows, list) and rows and isinstance(rows[0], list):
            body_rows = rows  # type: ignore
        elif isinstance(rows, list):
            body_rows = [rows]  # type: ignore

    children: list[str] = []

    if title:
        children.append(h("caption", children=title))

    if header_rows:
        thead_children: list[str] = []
        for hr in header_rows:
            # 当单元值没有被 th 包裹时，进行包装
            wrapped_cells = [
                cell if isinstance(cell, str) and cell.startswith("<th") else th(cell)
                for cell in hr
            ]
            th_cells = "".join(wrapped_cells)
            thead_children.append(tr(th_cells))
        children.append(h("thead", children="".join(thead_children)))

    if body_rows:
        tbody_children: list[str] = []
        for br in body_rows:
            # ensure each row is a list of cells
            cells = br if isinstance(br, list) else [br]
            # 当单元值没有被 td 包裹时，进行包装
            wrapped_cells = [
                cell if isinstance(cell, str) and cell.startswith("<td") else td(cell)
                for cell in cells
            ]
            td_cells = "".join(wrapped_cells)
            tbody_children.append(tr(td_cells))
        children.append(h("tbody", children="".join(tbody_children)))

    return h("table", children=children, classes=classes, props=props, persist=persist)


def Table(
    headers: list[list[str | float]] | list[str | float],
    rows: list[list[str | float]] | list[str | float],
    classes: str | None = None,
    *,
    title: str | None = None,
    props: Props | None = None,
):
    """
    Render an HTML table.

    - headers: either a list of header strings (one header row) or a list of header rows (list of list).
    - rows: either a list of cell strings (one body row) or a list of body rows (list of list).
    - title: optional caption for the table.
    """

    table(
        headers=headers,
        rows=rows,
        title=title,
        classes=classes,
        props=props,
        persist=True,
    )


def th(
    value: str,
    classes: str | None = None,
    *,
    rowspan: int = 1,
    colspan: int = 1,
):
    return h(
        "th",
        children=value,
        classes=classes,
        props=props(rowspan=rowspan, colspan=colspan),
        persist=False,
    )


def tr(value: str, classes: str | None = None):
    return h(
        "tr",
        children=value,
        classes=classes,
        persist=False,
    )


def td(value: str, classes: str | None = None):
    return h(
        "td",
        children=value,
        classes=classes,
        persist=False,
    )


def input(content: str, persist: bool = False):
    """
    render an input
    :param content: input content
    """
    return h("input", props=props(custom={"value": content}), persist=persist)


def Input(content: str):
    """
    render an input
    :param content: input content
    """
    input(content, persist=True)


def code(content: str, language: str | None = None):
    """
    render inline code
    :param content: code content
    :param persist: if True, will append to the current document context
    """
    # 分割成行并添加行号
    lines = content.split("\n")
    # 去掉首尾空行
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()

    # 如果指定了语言，添加language-xxx类以支持highlight.js
    lang_class = f"language-{language}" if language else ""
    code_html = h(
        "code",
        children=str.join("\n", [line for line in lines]),
        classes=lang_class,
    )
    pre_html = h("pre", children=code_html)
    return pre_html


def Code(content: str, language: str | None = None):
    """
    render a code block with syntax highlighting
    :param content: code content
    :param language: programming language for syntax highlighting (e.g., 'python', 'javascript', 'html')
    """
    pre_html = code(content, language=language)
    ctx = get_current_instance()
    ctx.append_content(pre_html)


def info(content: str, persist: bool = False):
    """
    render an info box
    :param content: info box content
    """
    return div(
        content,
        classes="flex flex-row items-center bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded relative",
        persist=persist,
    )


def Info(content: str):
    """
    render an info box
    :param content: info box content
    """
    info(content, persist=True)


def laTex(content: str, persist: bool = False):
    """
    内容为 latex 语法，渲染为 mathML 格式
    :param content: latex content
    """
    return h("latex", children=content, props=None, persist=persist)


def LaTex(content: str):
    """
    内容为 latex 语法，渲染为 mathML 格式
    :param content: latex content
    """
    laTex(content, persist=True)


def plot(fig: Figure, persist: bool = False):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    svg_bytes = buf.getvalue()
    svg_base64 = base64.b64encode(svg_bytes).decode("ascii")
    svg_data_uri = f"data:image/png;base64,{svg_base64}"
    return img(svg_data_uri, persist=persist)


def Plot(fig: Figure | bytes):
    """
    render a matplotlib figure as an embedded image
    :param fig: matplotlib Figure object
    """

    if isinstance(fig, bytes):
        import base64

        svg_base64 = base64.b64encode(fig).decode("ascii")
        svg_data_uri = f"data:image/png;base64,{svg_base64}"
        Img(svg_data_uri)
    else:
        plot(fig, persist=True)
