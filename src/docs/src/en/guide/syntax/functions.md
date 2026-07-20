---
title: Letters and Function Styles
icon: function
order: 7
---

## Greek Letter Conversion

UzonCalc renders common Greek letter names as symbols. For example, `alpha`, `beta`, `gamma`, and `delta` are displayed as Greek letters.

Names starting with a lowercase letter are rendered as lowercase Greek letters. Names starting with an uppercase letter are rendered as uppercase Greek letters:

```python
rho_water = 1000 * unit.kilogram / unit.meter**3
gamma_0 = 9.81 * unit.meter / unit.second**2
```

If you do not want a name to be converted, escape it with a backslash.

## Square Root

`sqrt(x)` is rendered with square-root notation:

```python
edge1 = 3 * unit.meter
edge2 = 4 * unit.meter
diagonal = sqrt(edge1**2 + edge2**2)
```

## Absolute Value

`abs(x)` is rendered as an absolute value:

```python
value = -15 * unit.newton
abs_value = abs(value)
```

## Escaping Text

Variable names, Greek letter names, and underscore rules affect formula rendering. Use a backslash when you need to keep the original characters, for example `\alpha`.
