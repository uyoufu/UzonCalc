---
title: Variables and Formulas
icon: square-root-variable
order: 2
---

## Numeric Types

Numbers are written directly without quotes, following Python syntax:

```python
integer_number = 100
float_number = 3.1415
scientific_number = 1.2e3
complex_number = 2 + 3j
```

UzonCalc records assignment statements and renders formulas, substituted values, and calculation results in the report.

## Operations and Comparisons

Use standard Python operators for calculations:

```python
operator_result = (5 + 3) * 2 - 4 / 2**2
comparison_result = (5 > 3) and (2 == 2) or (4 != 5)
```

Common operators include:

- `+`, `-`, `*`, `/`: addition, subtraction, multiplication, and division
- `**`: exponentiation
- `>`, `<`, `>=`, `<=`, `==`, `!=`: comparisons

## Using Variables

Variables store intermediate results, avoid repeated input, and make formulas closer to engineering notation:

```python
N_s = 100 * unit.kN
A_s = 50 * unit.mm**2
sigma_s = N_s / A_s
```

UzonCalc displays variables in mathematical style and automatically substitutes values into formulas.

## Naming Variables

Variable names can contain letters, digits, and underscores, but cannot start with a digit.

Use meaningful English names where possible. Because `_` is used for subscript display, use camelCase if you do not want a subscript:

```python
beamLength = 6 * unit.m
designMoment = 120 * unit.kN * unit.m
```

Use underscores when you want mathematical symbols with subscripts:

```python
f_c = 30 * unit.MPa
gamma_0 = 9.81 * unit.meter / unit.second**2
```

## Aliases

Python variable names cannot directly express every display symbol. Use `alias()` when you need a friendlier display name:

```python
f_c = 30 * unit.MPa
alias("f_c", "Concrete strength grade")

f"Now the alias will be displayed: {f_c}"

alias("f_c", None)
f"The alias is removed, so the original name is displayed: {f_c}"
```

After an alias is defined, the variable is displayed with that alias until you remove it with `alias("variable_name", None)`.

## Input Variables

In UI mode, use `UI()` to create an input form:

```python
inputs = await UI(
    "Structural Parameters",
    [
        Field("width", "Width", FieldType.number, value=10),
        Field("length", "Length", FieldType.number, value=30),
        Field("height", "Height", FieldType.number, value=20),
    ],
)

f"The width is {inputs.width}, length is {inputs.length}, and height is {inputs.height}."
```

`UI()` pauses report execution, waits for user input, and returns the values for later calculations.
