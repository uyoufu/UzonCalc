from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, Protocol


@dataclass
class StepEvent:
    name: str
    expr: str
    value: Any
    substituted_expr: str | None
    is_constant: bool
    is_single_name: bool
    is_expr_stmt: bool
    is_quantity_literal: bool
    is_quantity: bool
    enable_substitution: bool
    rendered: str | None = None

    def render_segments(self) -> list[str]:
        """
        Return the ordered expression/value segments that should appear
        after the variable name for rendering.
        """
        if self.is_quantity and self.is_quantity_literal and not self.is_expr_stmt:
            return [str(self.value)]

        if self.is_constant and not self.is_expr_stmt:
            return [self.expr]

        if self.is_single_name:
            if self.is_expr_stmt:
                return [str(self.value)]
            return [self.expr, str(self.value)]

        if self.substituted_expr:
            return [self.expr, self.substituted_expr, str(self.value)]

        return [self.expr, str(self.value)]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StepRenderer(Protocol):
    def render(self, event: StepEvent) -> str: ...


RendererFactory = Callable[[], StepRenderer]


_RENDERERS: Dict[str, RendererFactory] = {}


def register_renderer(name: str, factory: RendererFactory) -> None:
    _RENDERERS[name] = factory


def resolve_renderer(renderer: str | StepRenderer | None) -> StepRenderer:
    if renderer is None:
        return TextStepRenderer()

    if hasattr(renderer, "render") and callable(getattr(renderer, "render")):
        return renderer  # type: ignore[return-value]

    if isinstance(renderer, str):
        factory = _RENDERERS.get(renderer)
        if factory is None:
            raise ValueError(f"Unknown renderer: {renderer}")
        return factory()

    raise TypeError("renderer must be a registered name or an object with render()")


class TextStepRenderer:
    def render(self, event: StepEvent) -> str:
        segments = event.render_segments()
        return f"{event.name} = " + " = ".join(segments)


class LatexStepRenderer:
    def render(self, event: StepEvent) -> str:
        segments = event.render_segments()
        if not segments:
            return f"{event.name} = "

        lines = []
        for idx, seg in enumerate(segments):
            if idx == 0:
                lines.append(f"{event.name} &= {seg}")
            else:
                lines.append(f"&= {seg}")
        body = " \\\\ ".join(lines)
        return f"\\begin{{aligned}} {body} \\end{{aligned}}"


class HtmlStepRenderer:
    def render(self, event: StepEvent) -> str:
        segments = event.render_segments()
        parts = [f'<span class="calc-step-name">{event.name}</span>']
        for seg in segments:
            parts.append('<span class="calc-step-equal">=</span>')
            parts.append(f'<span class="calc-step-part">{seg}</span>')
        inner = "".join(parts)
        return f'<div class="calc-step">{inner}</div>'


register_renderer("text", lambda: TextStepRenderer())
register_renderer("latex", lambda: LatexStepRenderer())
register_renderer("html", lambda: HtmlStepRenderer())

__all__ = [
    "StepEvent",
    "StepRenderer",
    "TextStepRenderer",
    "LatexStepRenderer",
    "HtmlStepRenderer",
    "register_renderer",
    "resolve_renderer",
]
