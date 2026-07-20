---
title: Text and Headings
icon: circle-info
order: 1
---

## Plain Text

In UzonCalc, strings wrapped in single quotes, double quotes, or triple quotes are emitted as body paragraphs:

```python
'Single-quoted text'

"Double-quoted text"

"""
Triple-quoted text,
line 1,
line 2
"""
```

Single and double quotes are suitable for one-line text. Triple quotes are suitable for longer paragraphs. Line breaks inside triple quotes are merged into one paragraph instead of forcing a new line for every source line.

::: info
All body text must be wrapped in quotes. This is required by Python syntax and is also how UzonCalc records document content.
:::

## Line Breaks

Use `Br()` when you need to insert a blank line intentionally:

```python
"First paragraph"
Br()
"Second paragraph"
```

## Headings

UzonCalc provides `Title()` and heading functions from `H1()` to `H6()`:

```python
Title("UzonCalc User Guide")

H2("Installation")
H3("CLI Installation")
```

Recommended usage:

- `Title()` for the cover or main report title.
- `H2()` for chapter headings.
- `H3()` for section headings.
- Lower-level headings only when the hierarchy really needs them.

Headings participate in table-of-contents generation and define the document hierarchy.

## Markdown

Use `Markdown()` for richer text such as lists, links, and emphasis:

```python
Markdown("""
- **AI friendly**: the calculation process is Python code
- **Automatic typesetting**: chapter and figure numbers are generated automatically
- **Multi-format output**: supports PDF, Word, and other documents
""")
```

## Code Blocks

Use `Code()` to emit code blocks:

```python
Code(
    """
from uzoncalc import *

@uzon_calc()
async def sheet():
    doc_title("example")
    "Hello, UzonCalc!"
""",
    "python",
)
```

The second argument specifies the language for syntax highlighting.
