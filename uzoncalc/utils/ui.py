from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Field:
    name: str
    type: str
    label: str
    default: str | int | float | bool | None = None
    options: list[str] | None = None
    vif: str | None = None


@dataclass(frozen=True, slots=True)
class Window:
    title: str
    fields: list[Field]
