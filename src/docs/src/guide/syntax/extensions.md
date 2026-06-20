---
title: Excel 与扩展
icon: table
order: 9
---

## Excel 复用

UzonCalc 支持调用 Excel 中已有的计算模型，并将结果摘录到计算书中。这适合已有 Excel 模型较成熟、短期内不希望全部迁移为 Python 的场景。

```python
from uzoncalc.extension.excel import get_excel_table
```

使用时建议把 Excel 输入、计算和摘录结果分成清晰步骤，避免让计算书正文混入过多临时操作。

## JavaScript 图表扩展

可以通过 `uzoncalc.extension.echarts` 使用 ECharts：

```python
from uzoncalc.extension.echarts import EChart
```

如果图表配置较复杂，建议先在 ECharts 官方示例中调好 `options`，再复制到计算书中。

## 隐藏中间过程

某些变量只用于准备数据，不希望出现在计算书正文中时，可以使用 `hide()` 和 `show()` 控制显示：

```python
hide()
raw_data = [1, 2, 3]
chart_options = {"series": [{"type": "line", "data": raw_data}]}
show()

EChart(chart_options)
```

这能让报告保留关键计算过程，同时隐藏对读者无意义的中间代码。
