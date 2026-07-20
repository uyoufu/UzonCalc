"""DOM helpers shared by handcalc post handlers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, TypeAlias

import lxml.etree as etree
import lxml.html as lxml_html

HtmlPart: TypeAlias = str | etree._Element
FRAGMENT_ROOT_TAG = "uzoncalc-post-root"


@dataclass
class PostHandlerNode:
    """Wrap an lxml node with lazily cached tag-context lookups.

    Args:
        node: The lxml element currently being visited by the post-handler
            pipeline.

    Raises:
        None.
    """

    node: etree._Element
    _tag_name: str | None = field(default=None, init=False)
    _text_context_tag_names: tuple[str, ...] | None = field(default=None, init=False)
    _tail_context_tag_names: tuple[str, ...] | None = field(default=None, init=False)

    @property
    def tag_name(self) -> str:
        """Return the current element tag name.

        Returns:
            The lowercase local tag name, or an empty string for non-element
            nodes.

        Raises:
            None.
        """
        if self._tag_name is None:
            self._tag_name = self._get_element_tag_name(self.node)
        return self._tag_name

    @property
    def text_context_tag_names(self) -> tuple[str, ...]:
        """Return tag names that own the node text context.

        Returns:
            The current node tag followed by ancestor tag names.

        Raises:
            None.
        """
        if self._text_context_tag_names is None:
            self._text_context_tag_names = tuple(
                self._iter_context_tag_names(self.node)
            )
        return self._text_context_tag_names

    @property
    def tail_context_tag_names(self) -> tuple[str, ...]:
        """Return tag names that own the node tail context.

        Returns:
            The parent tag followed by ancestor tag names. Detached nodes and
            root-level tails return an empty tuple.

        Raises:
            None.
        """
        if self._tail_context_tag_names is None:
            text_context_tag_names = self.text_context_tag_names
            self._tail_context_tag_names = (
                text_context_tag_names[1:] if self.tag_name else text_context_tag_names
            )
        return self._tail_context_tag_names

    def is_text_in_tag_context(self, tag_names: set[str]) -> bool:
        """Return whether node text belongs to one of the provided tags.

        Args:
            tag_names: Lowercase HTML tag names that should be treated as
                protected text contexts.

        Returns:
            True when the node text context contains any provided tag.

        Raises:
            None.
        """
        return not tag_names.isdisjoint(self.text_context_tag_names)

    def is_tail_in_tag_context(self, tag_names: set[str]) -> bool:
        """Return whether node tail belongs to one of the provided tags.

        Args:
            tag_names: Lowercase HTML tag names that should be treated as
                protected tail contexts.

        Returns:
            True when the node tail context contains any provided tag.

        Raises:
            None.
        """
        return not tag_names.isdisjoint(self.tail_context_tag_names)

    def replace_text(
        self,
        transform: Callable[[str], str],
        *,
        skip_tags: set[str] | None = None,
    ) -> None:
        """Replace node text with a plain-text transform result.

        Args:
            transform: Function that receives and returns text content.
            skip_tags: Optional protected tag names for skipping this text
                context.

        Returns:
            None.

        Raises:
            Exceptions raised by ``transform`` are propagated.
        """
        if self.node.text is None:
            return
        if skip_tags and self.is_text_in_tag_context(skip_tags):
            return
        self.node.text = transform(self.node.text)

    def replace_tail(
        self,
        transform: Callable[[str], str],
        *,
        skip_tags: set[str] | None = None,
    ) -> None:
        """Replace node tail with a plain-text transform result.

        Args:
            transform: Function that receives and returns tail text.
            skip_tags: Optional protected tag names for skipping this tail
                context.

        Returns:
            None.

        Raises:
            Exceptions raised by ``transform`` are propagated.
        """
        if self.node.tail is None:
            return
        if skip_tags and self.is_tail_in_tag_context(skip_tags):
            return
        self.node.tail = transform(self.node.tail)

    def replace_text_with_parts(
        self,
        parts: Iterable[HtmlPart],
        *,
        skip_tags: set[str] | None = None,
    ) -> None:
        """Replace node text with text and element parts.

        Args:
            parts: Text and lxml element fragments to insert before existing
                child elements.
            skip_tags: Optional protected tag names for skipping this text
                context.

        Returns:
            None.

        Raises:
            Exceptions raised while iterating ``parts`` are propagated.
        """
        if skip_tags and self.is_text_in_tag_context(skip_tags):
            return
        self.node.text = None
        insert_index = 0
        tail_target = self.node
        writes_parent_text = True
        for part in parts:
            if isinstance(part, str):
                if not part:
                    continue
                if writes_parent_text:
                    self.node.text = (self.node.text or "") + part
                else:
                    tail_target.tail = (tail_target.tail or "") + part
                continue
            part.tail = None
            self.node.insert(insert_index, part)
            insert_index += 1
            tail_target = part
            writes_parent_text = False

    def replace_tail_with_parts(
        self,
        parts: Iterable[HtmlPart],
        *,
        skip_tags: set[str] | None = None,
    ) -> None:
        """Replace node tail with text and element parts.

        Args:
            parts: Text and lxml element fragments to insert after the current
                element.
            skip_tags: Optional protected tag names for skipping this tail
                context.

        Returns:
            None.

        Raises:
            Exceptions raised while iterating ``parts`` are propagated.
        """
        if skip_tags and self.is_tail_in_tag_context(skip_tags):
            return
        parent = self.node.getparent()
        if parent is None:
            return
        self.node.tail = None
        insert_index = parent.index(self.node) + 1
        tail_target = self.node
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

    def replace_with_element(self, replacement: etree._Element) -> None:
        """Replace the wrapped element in-place.

        Args:
            replacement: Element that should replace the wrapped node.

        Returns:
            None.

        Raises:
            None.
        """
        parent = self.node.getparent()
        if parent is None:
            return
        replacement.tail = self.node.tail
        parent.replace(self.node, replacement)

    def _iter_context_tag_names(self, node: etree._Element) -> Iterable[str]:
        """Yield lowercase tag names from a node through its ancestors.

        Args:
            node: Starting lxml element for the context lookup.

        Returns:
            An iterable of lowercase tag names, excluding non-element nodes.

        Raises:
            None.
        """
        current: etree._Element | None = node
        while current is not None:
            tag_name = self._get_element_tag_name(current)
            if tag_name:
                yield tag_name
            current = current.getparent()

    def _get_element_tag_name(self, node: etree._Element) -> str:
        """Return the lowercase local tag name for an lxml element.

        Args:
            node: lxml node whose tag should be normalized.

        Returns:
            Lowercase local tag name, or an empty string for non-element nodes.

        Raises:
            None.
        """
        if not isinstance(node.tag, str):
            return ""
        return node.tag.rsplit("}", 1)[-1].lower()


def parse_html_fragment(content: str) -> etree._Element:
    """Parse an HTML fragment or plain text into a temporary root element."""
    if content == "":
        return lxml_html.Element(FRAGMENT_ROOT_TAG)
    try:
        return lxml_html.fragment_fromstring(
            content,
            create_parent=FRAGMENT_ROOT_TAG,  # type: ignore[reportArgumentType]
        )
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
