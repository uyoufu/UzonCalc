from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from typing import Any, Callable, TypeVar

from . import ir


TNode = TypeVar("TNode", bound=ir.MathNode)


def transform_ir(
    node: TNode,
    transformer: Callable[[ir.MathNode], ir.MathNode | None],
    *,
    should_descend: Callable[[ir.MathNode, str], bool] | None = None,
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
            new_v = (
                transform_ir(v, transformer, should_descend=should_descend)
                if should_descend is None or should_descend(node, f.name)
                else v
            )
            updated[f.name] = new_v
            changed = changed or (new_v is not v)
            continue

        if isinstance(v, list) and all(isinstance(ch, ir.MathNode) for ch in v):
            if should_descend is None or should_descend(node, f.name):
                new_list = [
                    transform_ir(ch, transformer, should_descend=should_descend)
                    for ch in v
                ]
            else:
                new_list = v
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
