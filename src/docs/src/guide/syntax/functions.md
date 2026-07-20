---
title: 字母与函数样式
icon: function
order: 7
---

## 希腊字母转换

UzonCalc 会将常见希腊字母英文名渲染为对应符号。例如 `alpha`、`beta`、`gamma`、`delta` 会显示为希腊字母。

以小写字母开头的名称会渲染为小写希腊字母，以大写字母开头的名称会渲染为大写希腊字母：

```python
rho_water = 1000 * unit.kilogram / unit.meter**3
gamma_0 = 9.81 * unit.meter / unit.second**2
```

如果不希望某个名称被转换，可以在名称前添加反斜杠进行转义。

## 平方根

`sqrt(x)` 会按平方根样式渲染：

```python
edge1 = 3 * unit.meter
edge2 = 4 * unit.meter
diagonal = sqrt(edge1**2 + edge2**2)
```

## 绝对值

`abs(x)` 会按绝对值样式渲染：

```python
value = -15 * unit.newton
abs_value = abs(value)
```

## 字符串转义

变量名、希腊字母名称和下划线规则会影响公式显示。如果需要保持原始字符，可以使用反斜杠转义，例如 `\alpha`。
