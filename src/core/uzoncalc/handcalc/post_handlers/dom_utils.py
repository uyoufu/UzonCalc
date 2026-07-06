"""DOM helpers shared by handcalc post handlers."""

from __future__ import annotations

from typing import Callable, Iterable, TypeAlias

from lxml import etree
from lxml import html as lxml_html

HtmlPart: TypeAlias = str | etree._Element
FRAGMENT_ROOT_TAG = "uzoncalc-post-root"


def parse_html_fragment(content: str) -> etree._Element:
    """Parse an HTML fragment or plain text into a temporary root element."""
    if content == "":
        return lxml_html.Element(FRAGMENT_ROOT_TAG)
    try:
        return lxml_html.fragment_fromstring(content, create_parent=FRAGMENT_ROOT_TAG)
    except (etree.ParserError, ValueError):
        root = lxml_html.Element(FRAGMENT_ROOT_TAG)
        root.text = content
        return root


def serialize_html_fragment(root: etree._Element) -> str:
    """Serialize a temporary root element back to an HTML fragment string.

    lxml's native HTML serializer is substantially faster than the previous
    Python recursion. The temporary wrapper is stripped after one full-tree
    serialization so callers still receive an HTML fragment.
    """
    serialized_root = etree.tostring(root, encoding="unicode", method="html")
    open_wrapper = f"<{FRAGMENT_ROOT_TAG}>"
    close_wrapper = f"</{FRAGMENT_ROOT_TAG}>"
    if serialized_root.startswith(open_wrapper) and serialized_root.endswith(
        close_wrapper
    ):
        return serialized_root[len(open_wrapper) : -len(close_wrapper)]
    return serialized_root


def element_tag_name(node: etree._Element) -> str:
    """Return the lowercase local tag name for an lxml element."""
    if not isinstance(node.tag, str):
        return ""
    return node.tag.rsplit("}", 1)[-1].lower()


def is_text_in_tag_context(node: etree._Element, tag_names: set[str]) -> bool:
    """Return whether node text belongs to a skipped element context."""
    current: etree._Element | None = node
    while current is not None:
        if element_tag_name(current) in tag_names:
            return True
        current = current.getparent()
    return False


def is_tail_in_tag_context(node: etree._Element, tag_names: set[str]) -> bool:
    """Return whether node tail belongs to a skipped parent context."""
    parent = node.getparent()
    if parent is None:
        return False
    return is_text_in_tag_context(parent, tag_names)


def replace_node_text(
    node: etree._Element,
    transform: Callable[[str], str],
    *,
    skip_tags: set[str] | None = None,
) -> None:
    """Replace node text with a plain-text transform result."""
    if node.text is None:
        return
    if skip_tags and is_text_in_tag_context(node, skip_tags):
        return
    node.text = transform(node.text)


def replace_node_tail(
    node: etree._Element,
    transform: Callable[[str], str],
    *,
    skip_tags: set[str] | None = None,
) -> None:
    """Replace node tail with a plain-text transform result."""
    if node.tail is None:
        return
    if skip_tags and is_tail_in_tag_context(node, skip_tags):
        return
    node.tail = transform(node.tail)


def replace_node_text_with_parts(
    node: etree._Element,
    parts: Iterable[HtmlPart],
) -> None:
    """Replace node text with text/element parts inserted before children."""
    node.text = None
    insert_index = 0
    tail_target = node
    writes_parent_text = True
    for part in parts:
        if isinstance(part, str):
            if not part:
                continue
            if writes_parent_text:
                node.text = (node.text or "") + part
            else:
                tail_target.tail = (tail_target.tail or "") + part
            continue
        part.tail = None
        node.insert(insert_index, part)
        insert_index += 1
        tail_target = part
        writes_parent_text = False


def replace_node_tail_with_parts(
    node: etree._Element,
    parts: Iterable[HtmlPart],
) -> None:
    """Replace node tail with text/element parts inserted after the node."""
    parent = node.getparent()
    if parent is None:
        return
    node.tail = None
    insert_index = parent.index(node) + 1
    tail_target = node
    for part in parts:
        if isinstance(part, str):
            if not part:
                continue
            tail_target.tail = (tail_target.tail or "") + part
            continue
        part.tail = None
        parent.insert(insert_index, part)
        insert_index += 1
        tail_target = part


def replace_node_with_element(
    node: etree._Element,
    replacement: etree._Element,
) -> None:
    """Replace an element in-place while preserving its tail text."""
    parent = node.getparent()
    if parent is None:
        return
    replacement.tail = node.tail
    parent.replace(node, replacement)
