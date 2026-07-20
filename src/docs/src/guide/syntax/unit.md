---
title: 单位
icon: circle-info
order: 4
---

## 使用单位

UzonCalc 使用 `pint` 作为单位计算引擎。你可以通过 `unit.*` 使用单位：

```python
length = 5 * unit.meter
width = 10 * unit.m
height = 2 * unit.meter
volume = length * width * height
```

常用单位可以使用全名，也可以使用缩写。具体单位列表可参考 [Pint 默认单位定义](https://github.com/hgrecco/pint/blob/master/pint/default_en.txt)。

## 单位计算

带单位的量可以直接进行加、减、乘、除、幂和开方等运算：

```python
force = 100 * unit.newton
area = length * width
stress = force / area

sqrt_area = sqrt(area + 10 * unit.meter**2)
acceleration = force * 1000 / (10 * unit.kilogram)
```

同一量纲的不同单位可以直接计算，UzonCalc 会自动处理换算：

```python
total_length = 10 * unit.m + 20 * unit.cm
```

## 单位转换

使用 `to()` 方法可以将结果转换为指定单位：

```python
speed_m_per_s = 18 * unit.meter / unit.second
speed_km_per_h = speed_m_per_s.to(unit.kilometer / unit.hour)

"单位转换前，速度 (m/s):"
speed_m_per_s

"单位转换后，速度 (km/h):"
speed_km_per_h
```

## 编写建议

- 计算过程中优先保留单位，不要过早换成纯数字。
- 只有在输出需要固定单位时，再用 `to()` 转换。
- 同一变量命名中尽量体现业务含义，例如 `design_force`、`beam_length`。
