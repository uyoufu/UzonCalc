---
title: Formatter 与数值显示
icon: wand-magic-sparkles
order: 5
---

## 代码格式化 Formatter

UzonCalc 的编辑器和接口支持使用 Black 格式化 Python 代码。格式化不会改变计算书的业务逻辑，只会统一缩进、换行和代码布局。

接口使用的 formatter 名称为 `black`，默认行宽为 `88`：

```json
{
  "code": "from uzoncalc import *\n",
  "lineLength": 88
}
```

返回结果中会包含：

```json
{
  "formattedCode": "from uzoncalc import *\n",
  "changed": false,
  "formatter": "black"
}
```

在桌面端编辑器中，可以使用编辑器的格式化命令整理当前计算书代码。

::: tip
建议在保存或提交计算书前格式化代码。统一格式可以让 AI 修改、人工审查和版本比较更稳定。
:::

## f-string 格式化

Python f-string 支持在 `{}` 中使用格式化规范，例如保留小数位：

```python
pi = 3.1415926535
f"Value of pi up to 3 decimal places: {pi:.3f}"
```

`:.3f` 表示按浮点数显示并保留 3 位小数。UzonCalc 会在渲染 f-string 时应用该格式。

## 带单位数值的格式化

对带单位的量使用 f-string 格式化时，UzonCalc 会格式化数值部分并保留单位：

```python
width = 10.12345 * unit.meter
f"宽度为 {width:.2f}"
```

这适合控制报告中的展示精度。

## f-string 中显示公式

默认情况下，f-string 中的表达式只显示结果。若希望同时显示公式和计算过程，可以启用 f-string 公式渲染：

```python
enable_fstring_equation()

width = 10 * unit.meter
length = 20 * unit.meter
f"Area is calculated as {width * length}."

disable_fstring_equation()
```

启用后，f-string 中的表达式会按公式渲染，直到调用 `disable_fstring_equation()` 关闭。

## f-string 计算结果赋值

可以使用海象运算符 `:=` 将 f-string 中表达式的结果赋值给变量：

```python
f"Area is calculated as {(temp_area := width * length)}."

enable_fstring_equation()
f"Area is calculated as {(temp_area := width * length)}."
disable_fstring_equation()

temp_area
```

这种写法适合在正文中解释计算过程，同时把结果留给后续计算使用。
