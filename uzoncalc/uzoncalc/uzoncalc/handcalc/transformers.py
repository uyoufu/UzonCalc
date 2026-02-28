from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from typing import Any, Callable, TypeVar

from . import ir


TNode = TypeVar("TNode", bound=ir.MathNode)


def transform_ir(
    node: TNode,
    transformer: Callable[[ir.MathNode], ir.MathNode | None],
) -> TNode:
    """
    Generic IR tree transformer.

    - Calls `transformer` on each node (pre-order).
    - If transformer returns a non-None value, that value replaces the node.
    - Otherwise, recursively transforms children and reconstructs the dataclass.

    This keeps node-specific recursion out of business logic (e.g. substitution).
    """

    replaced = transformer(node)
    if replaced is not None:
        return replaced  # type: ignore[return-value]

    if not is_dataclass(node):
        return node

    updated: dict[str, Any] = {}
    changed = False

    for f in fields(node):
        v = getattr(node, f.name)

        if isinstance(v, ir.MathNode):
            new_v = transform_ir(v, transformer)
            updated[f.name] = new_v
            changed = changed or (new_v is not v)
            continue

        if isinstance(v, list) and all(isinstance(ch, ir.MathNode) for ch in v):
            new_list = [transform_ir(ch, transformer) for ch in v]
            updated[f.name] = new_list
            changed = changed or any(n is not o for n, o in zip(new_list, v))
            continue

        updated[f.name] = v

    if not changed:
        return node

    try:
        return replace(node, **updated)  # type: ignore[return-value]
    except Exception:
        # Fallback: if reconstruction fails, return original to avoid breaking.
        return node
