---
title: Subscripts and Arrays
icon: subscript
order: 3
---

## Default Subscript Rules

Underscores in variable names are rendered as subscripts. For example, `H_2` is displayed as `H₂`.

```python
a_x = 10 * unit.meter / unit.second**2
speed_car = a_x * 2 * unit.second
```

This is useful for engineering formula notation.

## Non-ASCII Subscripts

Python variable names cannot directly contain arbitrary non-ASCII characters. Use aliases when you need Chinese characters or other symbols as subscripts:

```python
alias("speed_car", "speed_car")
f"Now the aliased subscript is displayed: {speed_car}"

distance = speed_car * 5 * unit.second

alias("speed_car", None)
f"The alias is removed, and speed_car is displayed with its original name: {speed_car}"
```

## Array Subscripts

For arrays and lists, UzonCalc automatically treats the content inside `[]` as subscripts:

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

## Multidimensional Arrays

Multidimensional arrays are often called tensors. They can represent scalars, vectors, matrices, and higher-dimensional data. UzonCalc supports tensor calculations with NumPy:

```python
arr = np.array([[1, 2, 3], [4, 5, 6]])
first_row = arr[0, :]
second_column = arr[:, 1]
first_cell = arr[0, 0]
```

UzonCalc renders variables in mathematical style: ordinary variables use italic text, and tensors with more than one dimension use bold upright text, matching common notation in papers.
