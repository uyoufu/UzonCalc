import base64
import io
from typing import List

from matplotlib.figure import Figure

from core.setup import get_current_instance


def h(
    tag: str,
    children: str | List[str] | None = None,
    *,
    props: dict | None = None,
    prevent: bool = False,
) -> str:
    """
    Create an HTML string representation.

    :param tag: The HTML tag name (e.g., 'div', 'span').
    :param children: A string or a list of child elements.
    :param props: A dictionary of attributes (e.g., {'class': 'example'}).
    :param prevent: If True, do not append to the current context.
    :return: A string representing the HTML.
    """
    props = props or {}
    children = children or []

    # Convert props dictionary to HTML attributes
    props_str = " ".join(f"{key}='{value}'" for key, value in props.items())
    props_str = f" {props_str}" if props_str else ""

    # Handle children
    if isinstance(children, list):
        children_str = "".join(children)
    else:
        children_str = children

    # the HTML string
    html_result = f"<{tag}{props_str}>{children_str}</{tag}>"

    if not prevent:
        ctx = get_current_instance()
        ctx.append_content(html_result)

    return html_result


def h1(
    content: str | List[str],
    *,
    props: dict | None = None,
    prevent: bool = False,
) -> str:
    """
    render a level 1 heading
    :param content: heading content
    """
    return h(
        "h1",
        children=content,
        props=props,
        prevent=prevent,
    )


def p(
    content: str | List[str],
    *,
    props: dict | None = None,
    prevent: bool = False,
) -> str:
    """
    render a paragraph
    :param content: paragraph content
    """
    return h("p", children=content, props=props, prevent=prevent)


def div(
    content: str | List[str],
    *,
    props: dict | None = None,
    prevent: bool = False,
):
    """
    render a div
    :param content: div content
    """
    h("div", children=content, props=props, prevent=prevent)


def span(
    content: str | List[str],
    *,
    props: dict | None = None,
    prevent: bool = False,
):
    """
    render a span
    :param content: span content
    """
    h("span", children=content, props=props, prevent=prevent)


def row(
    content: str | List[str],
    *,
    props: dict | None = None,
    prevent: bool = False,
    tag: str = "div",
):
    """
    render a row
    :param content: row content
    """
    return h(tag, children=content, props=props, prevent=prevent)


def input(content: str):
    """
    render an input
    :param content: input content
    """
    h("input", props={"value": content})


def laTex(content: str):
    """
    内容为 latex 语法，渲染为 mathML 格式
    :param content: latex content
    """
    h("latex", children=content)


def plot(fig: Figure):
    # 更常见做法：
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    svg_bytes = buf.getvalue()
    svg_base64 = base64.b64encode(svg_bytes).decode("ascii")
    svg_data_uri = f"data:image/png;base64,{svg_base64}"
    h("img", {"src": svg_data_uri})
