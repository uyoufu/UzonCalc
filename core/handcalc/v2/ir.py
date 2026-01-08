from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, List, Union


# Math IR node definitions
# ============================
# These are simple dataclasses representing MathML-like structures.
# They are intended to be easily constructed during AST-to-IR conversion
# and easily rendered into MathML later.
# ============================


@dataclass(frozen=True, slots=True)
class MathNode:
    """Base type for Math IR nodes."""


Math = Union[MathNode, str]


@dataclass(frozen=True, slots=True)
class Mi(MathNode):
    name: str
    tag: ClassVar[str] = "mi"


@dataclass(frozen=True, slots=True)
class Mn(MathNode):
    value: str
    tag: ClassVar[str] = "mn"


@dataclass(frozen=True, slots=True)
class Mo(MathNode):
    symbol: str
    tag: ClassVar[str] = "mo"


@dataclass(frozen=True, slots=True)
class MText(MathNode):
    text: str
    tag: ClassVar[str] = "mtext"


@dataclass(frozen=True, slots=True)
class MRow(MathNode):
    children: List[Math]
    tag: ClassVar[str] = "mrow"


@dataclass(frozen=True, slots=True)
class MFrac(MathNode):
    numerator: Math
    denominator: Math
    tag: ClassVar[str] = "mfrac"


@dataclass(frozen=True, slots=True)
class MSup(MathNode):
    base: Math
    exponent: Math
    tag: ClassVar[str] = "msup"


@dataclass(frozen=True, slots=True)
class MSub(MathNode):
    base: Math
    subscript: Math
    tag: ClassVar[str] = "msub"


@dataclass(frozen=True, slots=True)
class MSqrt(MathNode):
    body: Math
    tag: ClassVar[str] = "msqrt"


@dataclass(frozen=True, slots=True)
class MFenced(MathNode):
    body: Math
    open: str = "("
    close: str = ")"
    tag: ClassVar[str] = "mfenced"


def mi(name: str) -> Mi:
    return Mi(name=name)


def mn(value: Any) -> Mn:
    return Mn(value=str(value))


def mo(symbol: str) -> Mo:
    return Mo(symbol=symbol)


def mtext(text: str) -> MText:
    return MText(text=text)


def mrow(children: List[Math]) -> MRow:
    return MRow(children=children)


def mfrac(num: Math, den: Math) -> MFrac:
    return MFrac(numerator=num, denominator=den)


def msup(base: Math, exp: Math) -> MSup:
    return MSup(base=base, exponent=exp)


def msub(base: Math, sub: Math) -> MSub:
    return MSub(base=base, subscript=sub)


def msqrt(body: Math) -> MSqrt:
    return MSqrt(body=body)


def mfenced(body: Math, *, open: str = "(", close: str = ")") -> MFenced:
    return MFenced(body=body, open=open, close=close)


def is_node(obj: Any) -> bool:
    return isinstance(obj, MathNode)
