---
title: Units
icon: circle-info
order: 4
---

## Using Units

UzonCalc uses `pint` as its unit calculation engine. Use units through `unit.*`:

```python
length = 5 * unit.meter
width = 10 * unit.m
height = 2 * unit.meter
volume = length * width * height
```

Common units can be written as full names or abbreviations. See the [Pint default unit definitions](https://github.com/hgrecco/pint/blob/master/pint/default_en.txt) for the full list.

## Unit Calculations

Quantities with units can be added, subtracted, multiplied, divided, raised to powers, and passed through square roots:

```python
force = 100 * unit.newton
area = length * width
stress = force / area

sqrt_area = sqrt(area + 10 * unit.meter**2)
acceleration = force * 1000 / (10 * unit.kilogram)
```

Different units with the same dimension can be calculated directly. UzonCalc handles conversion automatically:

```python
total_length = 10 * unit.m + 20 * unit.cm
```

## Unit Conversion

Use `to()` to convert a result to another unit:

```python
speed_m_per_s = 18 * unit.meter / unit.second
speed_km_per_h = speed_m_per_s.to(unit.kilometer / unit.hour)

"Before conversion, speed (m/s):"
speed_m_per_s

"After conversion, speed (km/h):"
speed_km_per_h
```

## Writing Tips

- Keep units in calculations instead of converting to plain numbers too early.
- Convert with `to()` only when the output needs a fixed unit.
- Use variable names that express business meaning, such as `design_force` and `beam_length`.
