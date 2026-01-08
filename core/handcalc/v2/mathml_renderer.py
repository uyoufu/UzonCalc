from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from . import ir


_MATHML_NS = "http://www.w3.org/1998/Math/MathML"


def _el(tag: str, text: str | None = None, **attrib: str) -> ET.Element:
    e = ET.Element(tag, attrib=attrib)
    if text is not None:
        e.text = text
    return e


def render_math(node: ir.Math) -> ET.Element:
    """Render a Math IR node into a MathML Element (without <math> root)."""

    if isinstance(node, str):
        return _el("mtext", node)

    if isinstance(node, ir.Mi):
        return _el(node.tag, node.name)

    if isinstance(node, ir.Mn):
        return _el(node.tag, node.value)

    if isinstance(node, ir.Mo):
        return _el(node.tag, node.symbol)

    if isinstance(node, ir.MText):
        return _el(node.tag, node.text)

    if isinstance(node, ir.MRow):
        e = _el(node.tag)
        for ch in node.children:
            e.append(render_math(ch))
        return e

    if isinstance(node, ir.MFrac):
        e = _el(node.tag)
        e.append(_wrap_row(node.numerator))
        e.append(_wrap_row(node.denominator))
        return e

    if isinstance(node, ir.MSup):
        e = _el(node.tag)
        e.append(_wrap_row(node.base))
        e.append(_wrap_row(node.exponent))
        return e

    if isinstance(node, ir.MSub):
        e = _el(node.tag)
        e.append(_wrap_row(node.base))
        e.append(_wrap_row(node.subscript))
        return e

    if isinstance(node, ir.MSqrt):
        e = _el(node.tag)
        e.append(_wrap_row(node.body))
        return e

    if isinstance(node, ir.MFenced):
        e = _el(node.tag, open=node.open, close=node.close)
        e.append(_wrap_row(node.body))
        return e

    # Unknown node: stringify.
    return _el("mtext", str(node))


def render_equation(parts: list[ir.Math]) -> str:
    """Render a single line equation as <math><mrow>...</mrow></math> (no <p> wrapper)."""

    ET.register_namespace("", _MATHML_NS)
    math = ET.Element("math", attrib={"xmlns": _MATHML_NS})
    row = _el("mrow")

    for idx, part in enumerate(parts):
        if idx:
            row.append(_el("mo", "="))
        row.append(_wrap_row(part))

    math.append(row)
    return ET.tostring(math, encoding="unicode", method="xml")


def _wrap_row(node: Any) -> ET.Element:
    e = render_math(node)
    # Keep <mrow> as-is. Wrap other atoms inside <mrow> for stable composition.
    if e.tag == "mrow":
        return e
    w = _el("mrow")
    w.append(e)
    return w
