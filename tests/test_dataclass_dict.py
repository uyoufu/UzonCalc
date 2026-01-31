from dataclasses import dataclass


class Field(dict):
    pass


@dataclass(frozen=True, slots=True)
class Window(dict):
    title: str
    fields: list[Field]
    caption: str | None = None


try:
    w = Window(title="test", fields=[])
    print(f"Created: {w}")
    print(f"Is instance of dict: {isinstance(w, dict)}")
    print(f"Dict content: {dict(w)}")
    print(f"Attribute title: {w.title}")
except Exception as e:
    print(f"Error: {e}")
