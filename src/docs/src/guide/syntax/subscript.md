---
title: 下标与数组
icon: subscript
order: 3
---

## 默认下标规则

变量名中的下划线会被渲染为下标。例如 `H_2` 会显示为 `H₂`。

```python
a_x = 10 * unit.meter / unit.second**2
speed_car = a_x * 2 * unit.second
```

这适合表达工程公式中的下标变量。

## 非 ASCII 下标

由于 Python 变量名限制，不能直接在变量名中使用任意非 ASCII 字符。需要中文或特殊字符作为下标时，可以配合别名：

```python
alias("speed_car", "speed_汽车")
f"现在将会输出别名下标: {speed_car}"

distance = speed_car * 5 * unit.second

alias("speed_car", None)
f"别名已移除, speed_car 变量恢复原名: {speed_car}"
```

## 数组下标

对于数组和列表，UzonCalc 会自动将 `[]` 内的索引内容作为下标处理：

```python
arr2d = np.array([[1, 2, 3], [4, 5, 6]])
first_row = arr2d[0, :]
second_column = arr2d[:, 1]
first_cell = arr2d[0, 0]

list1 = [10, 20]
list2 = [30, 40]
combined_list = list1 + list2
second_item = combined_list[1]
```

## 多维数组

多维数组通常称为张量，可以表示标量、向量、矩阵以及更高维度的数据。UzonCalc 支持使用 NumPy 进行张量计算：

```python
arr = np.array([[1, 2, 3], [4, 5, 6]])
first_row = arr[0, :]
second_column = arr[:, 1]
first_cell = arr[0, 0]
```

UzonCalc 会将变量按数学排版显示：普通变量使用斜体，大于 1 维的张量使用加粗正体，更接近论文中的书写习惯。
