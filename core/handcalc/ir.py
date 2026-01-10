from __future__ import annotations

import ast
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, ClassVar, List
import xml.etree.ElementTree as ET


# MathNode IR node definitions
# ============================
# These are simple dataclasses representing MathML-like structures.
# They are intended to be easily constructed during AST-to-IR conversion
# and easily rendered into MathML later.
# ============================


@dataclass(frozen=True, slots=True)
class MathNode:
    """Base type for MathNode IR nodes."""

    _MATHML_NS: ClassVar[str] = "http://www.w3.org/1998/Math/MathML"

    tag: ClassVar[str] = ""
    mathml_attrib: ClassVar[dict[str, str]] = {}
    single_primitive_payload: ClassVar[bool] = False

    def to_mathml_element(self) -> ET.Element:
        """
        Render this node into a MathML Element (without <math> root).
        Most nodes map directly to a MathML tag like <mi>, <mrow>, etc.
        """

        if not is_dataclass(self):
            e = ET.Element(MText.tag)
            e.text = str(self)
            return e

        tag = self.tag

        # Per-class default MathML attributes (e.g. units).
        attrib: dict[str, str] = dict(getattr(type(self), "mathml_attrib", {}) or {})

        node_fields = list(fields(self))

        # Leaf nodes: single primitive payload => element.text.
        # This must not trigger for nodes like MSqrt(body) which also have 1 field.
        if type(self).single_primitive_payload:
            if len(node_fields) != 1:
                # Defensive: keep structure consistent.
                e = ET.Element(tag, attrib=attrib)
                e.text = str(self)
                return e
            payload = getattr(self, node_fields[0].name)
            e = ET.Element(tag, attrib=attrib)
            e.text = str(payload)
            return e

        # Collect children vs primitive fields.
        primitive_attrib: dict[str, str] = {}
        child_values: list[Any] = []

        for f in node_fields:
            v = getattr(self, f.name)

            if isinstance(v, MathNode):
                child_values.append(v)
                continue

            if isinstance(v, list) and all(isinstance(ch, MathNode) for ch in v):
                child_values.extend(v)
                continue

            if v is None:
                continue

            primitive_attrib[f.name] = str(v)

        attrib.update(primitive_attrib)

        e = ET.Element(tag, attrib=attrib)

        # For stable composition, certain containers wrap child atoms into <mrow>.
        wrap_child = tag in {MFrac.tag, MSup.tag, MSub.tag, MSqrt.tag, MFenced.tag}

        for ch in child_values:
            if wrap_child:
                e.append(_wrap_row(ch))
            else:
                e.append(ch.to_mathml_element())

        return e

    def to_mathml_xml(self) -> str:
        """Render this node into a <math>...</math> XML string."""

        ET.register_namespace("", self._MATHML_NS)
        math = ET.Element("math", attrib={"xmlns": self._MATHML_NS})
        math.append(_wrap_row(self))
        return ET.tostring(math, encoding="unicode", method="xml")

    def to_python_ast(self, *, ir_var_name: str) -> ast.expr:
        """Convert this node into Python AST that reconstructs it at runtime."""

        if not is_dataclass(self):
            return ast.Constant(value=str(self))

        factory_name = type(self).__name__.lower()
        func = ast.Attribute(
            value=ast.Name(id=ir_var_name, ctx=ast.Load()),
            attr=factory_name,
            ctx=ast.Load(),
        )

        node_fields = list(fields(self))
        args: list[ast.expr] = []
        keywords: list[ast.keyword] = []

        # Leaf nodes: single primitive payload => positional argument.
        if type(self).single_primitive_payload:
            if len(node_fields) == 1:
                payload = getattr(self, node_fields[0].name)
                if payload is None or isinstance(payload, (str, int, float, bool)):
                    args.append(ast.Constant(value=payload))
                    return ast.Call(func=func, args=args, keywords=keywords)

        for f in node_fields:
            v = getattr(self, f.name)

            # Only MathNode (and lists of MathNode) are treated as positional children.
            if isinstance(v, MathNode):
                args.append(v.to_python_ast(ir_var_name=ir_var_name))
                continue

            if isinstance(v, list) and all(isinstance(ch, MathNode) for ch in v):
                args.append(
                    ast.List(
                        elts=[ch.to_python_ast(ir_var_name=ir_var_name) for ch in v],
                        ctx=ast.Load(),
                    )
                )
                continue

            if v is None or isinstance(v, (str, int, float, bool)):
                const_v: str | int | float | bool | None = v
            else:
                const_v = str(v)
            keywords.append(ast.keyword(arg=f.name, value=ast.Constant(value=const_v)))

        return ast.Call(func=func, args=args, keywords=keywords)


@dataclass(frozen=True, slots=True)
class MMath(MathNode):
    tag: ClassVar[str] = "math"
    children: List[MathNode]

    def to_mathml_xml(self) -> str:
        # Override: render children directly under <math> with correct xmlns.
        ET.register_namespace("", self._MATHML_NS)
        math = ET.Element("math", attrib={"xmlns": self._MATHML_NS})
        for ch in self.children:
            math.append(ch.to_mathml_element())
        return ET.tostring(math, encoding="unicode", method="xml")


@dataclass(frozen=True, slots=True)
class Mi(MathNode):
    name: str
    tag: ClassVar[str] = "mi"
    single_primitive_payload: ClassVar[bool] = True


@dataclass(frozen=True, slots=True)
class Mu(MathNode):
    """Marker class for math nodes that represent units."""

    name: str
    tag: ClassVar[str] = "mtext"
    mathml_attrib: ClassVar[dict[str, str]] = {"class": "unit", "mathvariant": "normal"}
    single_primitive_payload: ClassVar[bool] = True


@dataclass(frozen=True, slots=True)
class Mn(MathNode):
    value: str
    tag: ClassVar[str] = "mn"
    single_primitive_payload: ClassVar[bool] = True


@dataclass(frozen=True, slots=True)
class Mo(MathNode):
    symbol: str
    tag: ClassVar[str] = "mo"
    single_primitive_payload: ClassVar[bool] = True


@dataclass(frozen=True, slots=True)
class MText(MathNode):
    text: str
    tag: ClassVar[str] = "mtext"
    single_primitive_payload: ClassVar[bool] = True


@dataclass(frozen=True, slots=True)
class MRow(MathNode):
    children: List[MathNode]
    tag: ClassVar[str] = "mrow"


@dataclass(frozen=True, slots=True)
class MFrac(MathNode):
    numerator: MathNode
    denominator: MathNode
    tag: ClassVar[str] = "mfrac"


@dataclass(frozen=True, slots=True)
class MSup(MathNode):
    base: MathNode
    exponent: MathNode
    tag: ClassVar[str] = "msup"

    def to_mathml_element(self) -> ET.Element:
        e = ET.Element(self.tag)

        base_el = _wrap_row(self.base)
        if self._needs_parentheses_for_power_base(self.base):
            base_el = self._parenthesize(base_el)

        e.append(base_el)
        e.append(_wrap_row(self.exponent))
        return e

    @staticmethod
    def _needs_parentheses_for_power_base(node: MathNode) -> bool:
        """Return True if a power base should be rendered as (base)^exp.

        MathML's <msup> applies to the entire base element, but without explicit
        parentheses many renderers visually suggest the exponent applies only to the
        last atom (e.g. `5 m^2`). Adding parentheses makes intent unambiguous.
        """

        # Atomic bases don't need parentheses: x^2, 5^2, m^2.
        # power is mrow
        if node.single_primitive_payload:
            return False

        # Composite bases should be parenthesized: (a+b)^2, (5 m)^2, (a/b)^2.
        return True

    @staticmethod
    def _parenthesize(base_el: ET.Element) -> ET.Element:
        row = ET.Element(MRow.tag)
        left = ET.Element(Mo.tag)
        left.text = "("
        right = ET.Element(Mo.tag)
        right.text = ")"

        row.append(left)
        row.append(base_el)
        row.append(right)
        return row


@dataclass(frozen=True, slots=True)
class MSub(MathNode):
    base: MathNode
    subscript: MathNode
    tag: ClassVar[str] = "msub"


@dataclass(frozen=True, slots=True)
class MSqrt(MathNode):
    body: MathNode
    tag: ClassVar[str] = "msqrt"


@dataclass(frozen=True, slots=True)
class MFenced(MathNode):
    body: MathNode
    open: str = "("
    close: str = ")"
    tag: ClassVar[str] = "mfenced"


@dataclass(frozen=True, slots=True)
class Equation(MathNode):
    """Pseudo-node representing an equation line rendered as <math><mrow>...</mrow></math>."""

    parts: List[MathNode]

    def to_mathml_xml(self) -> str:
        ET.register_namespace("", self._MATHML_NS)
        math = ET.Element("math", attrib={"xmlns": self._MATHML_NS})
        row = ET.Element(MRow.tag)

        for idx, part in enumerate(self.parts):
            if idx:
                eq = ET.Element(Mo.tag)
                eq.text = "="
                row.append(eq)
            row.append(_wrap_row(part))

        math.append(row)
        return ET.tostring(math, encoding="unicode", method="xml")


def _wrap_row(node: MathNode) -> ET.Element:
    e = node.to_mathml_element()
    if e.tag == MRow.tag:
        return e
    w = ET.Element(MRow.tag)
    w.append(e)
    return w


def mi(name: str) -> Mi:
    return Mi(name=name)


def mu(name: str) -> Mu:
    return Mu(name=name)


def mn(value: Any) -> Mn:
    return Mn(value=str(value))


def mo(symbol: str) -> Mo:
    return Mo(symbol=symbol)


def mtext(text: str) -> MText:
    return MText(text=text)


def mrow(children: List[MathNode]) -> MRow:
    return MRow(children=children)


def mfrac(num: MathNode, den: MathNode) -> MFrac:
    return MFrac(numerator=num, denominator=den)


def msup(base: MathNode, exp: MathNode) -> MSup:
    return MSup(base=base, exponent=exp)


def msub(base: MathNode, sub: MathNode) -> MSub:
    return MSub(base=base, subscript=sub)


def msqrt(body: MathNode) -> MSqrt:
    return MSqrt(body=body)


def mfenced(body: MathNode, *, open: str = "(", close: str = ")") -> MFenced:
    return MFenced(body=body, open=open, close=close)


def equation(parts: List[MathNode]) -> Equation:
    return Equation(parts=parts)


def is_node(obj: Any) -> bool:
    return isinstance(obj, MathNode)
