---
title: Formatter and Numeric Display
icon: wand-magic-sparkles
order: 5
---

## Code Formatter

The UzonCalc editor and API support formatting Python code with Black. Formatting does not change report logic; it only normalizes indentation, line breaks, and code layout.

The API formatter name is `black`, and the default line length is `88`:

```json
{
  "code": "from uzoncalc import *\n",
  "lineLength": 88
}
```

The response includes:

```json
{
  "formattedCode": "from uzoncalc import *\n",
  "changed": false,
  "formatter": "black"
}
```

In the desktop editor, use the editor formatting command to format the current calculation report code.

::: tip
Format code before saving or committing reports. Consistent formatting makes AI edits, human review, and version comparison more reliable.
:::

## f-string Formatting

Python f-strings support format specifications inside `{}`, such as fixed decimal places:

```python
pi = 3.1415926535
f"Value of pi up to 3 decimal places: {pi:.3f}"
```

`:.3f` means rendering a floating-point number with 3 decimal places. UzonCalc applies this format when rendering f-strings.

## Formatting Values with Units

When a quantity with units is formatted in an f-string, UzonCalc formats the magnitude and keeps the unit:

```python
width = 10.12345 * unit.meter
f"Width is {width:.2f}"
```

This is useful for controlling display precision in reports.

## Showing Formulas in f-strings

By default, expressions inside f-strings only show results. Enable f-string equation rendering when you want to show the formula and calculation process:

```python
enable_fstring_equation()

width = 10 * unit.meter
length = 20 * unit.meter
f"Area is calculated as {width * length}."

disable_fstring_equation()
```

After enabling it, expressions inside f-strings are rendered as formulas until `disable_fstring_equation()` is called.

## Assigning Results in f-strings

Use the walrus operator `:=` to assign an expression result inside an f-string:

```python
f"Area is calculated as {(temp_area := width * length)}."

enable_fstring_equation()
f"Area is calculated as {(temp_area := width * length)}."
disable_fstring_equation()

temp_area
```

This is useful when the body text explains a calculation and the result is needed later.
