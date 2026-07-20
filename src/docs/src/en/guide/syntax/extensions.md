---
title: Excel and Extensions
icon: table
order: 9
---

## Excel Reuse

UzonCalc can call existing Excel calculation models and extract results into the report. This is useful when an Excel model is already mature and you do not want to migrate everything to Python immediately.

```python
from uzoncalc.extension.excel import get_excel_table
```

When using Excel integration, keep Excel input, calculation, and result extraction as clear separate steps. Avoid mixing too many temporary operations into the report body.

## JavaScript Chart Extensions

Use `uzoncalc.extension.echarts` for ECharts:

```python
from uzoncalc.extension.echarts import EChart
```

For complex chart options, configure the chart in the official ECharts examples first, then copy the final `options` into the report.

## Hiding Intermediate Steps

When variables are only used to prepare data and should not appear in the report body, use `hide()` and `show()`:

```python
hide()
raw_data = [1, 2, 3]
chart_options = {"series": [{"type": "line", "data": raw_data}]}
show()

EChart(chart_options)
```

This keeps the report focused on important calculation steps while hiding implementation details that readers do not need.
