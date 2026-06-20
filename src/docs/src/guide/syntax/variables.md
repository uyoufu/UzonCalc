---
title: 变量与公式
icon: square-root-variable
order: 2
---

## 数值类型

数值不需要引号，直接按 Python 语法书写：

```python
integer_number = 100
float_number = 3.1415
scientific_number = 1.2e3
complex_number = 2 + 3j
```

UzonCalc 会记录赋值语句，并在文档中渲染公式、代入值和计算结果。

## 运算与比较

可以使用标准 Python 运算符进行计算：

```python
operator_result = (5 + 3) * 2 - 4 / 2**2
comparison_result = (5 > 3) and (2 == 2) or (4 != 5)
```

常用运算符包括：

- `+`、`-`、`*`、`/`：加、减、乘、除
- `**`：幂运算
- `>`、`<`、`>=`、`<=`、`==`、`!=`：比较运算

## 使用变量

变量用于保存中间结果，避免重复输入，也能让公式更接近工程表达：

```python
N_s = 100 * unit.kN
A_s = 50 * unit.mm**2
sigma_s = N_s / A_s
```

在 UzonCalc 中，变量会以数学样式显示，变量值会自动代入公式。

## 变量命名

变量名可以包含字母、数字和下划线，但不能以数字开头。

推荐使用能表达业务含义的英文命名。由于 `_` 会被用于下标显示，如果不希望产生下标，可以使用 camelCase：

```python
beamLength = 6 * unit.m
designMoment = 120 * unit.kN * unit.m
```

如果你希望变量显示为带下标的数学符号，可以使用下划线：

```python
f_c = 30 * unit.MPa
gamma_0 = 9.81 * unit.meter / unit.second**2
```

## 变量别名

Python 变量名不能直接使用任意显示符号。需要更友好的显示名称时，可以使用 `alias()`：

```python
f_c = 30 * unit.MPa
alias("f_c", "混凝土强度等级")

f"现在将会输出别名: {f_c}"

alias("f_c", None)
f"别名已经取消，现在将会输出原名: {f_c}"
```

别名定义后，变量在文档中会以别名显示，直到使用 `alias("变量名", None)` 移除。

## 输入变量

在 UI 模式下，可以使用 `UI()` 创建输入窗体：

```python
inputs = await UI(
    "结构参数输入",
    [
        Field("width", "宽度", FieldType.number, value=10),
        Field("length", "长度", FieldType.number, value=30),
        Field("height", "高度", FieldType.number, value=20),
    ],
)

f"用户输入的宽度为 {inputs.width}，长度为 {inputs.length}，高度为 {inputs.height}。"
```

`UI()` 会暂停计算书执行，等待用户输入，再将输入结果作为返回值继续参与计算。
