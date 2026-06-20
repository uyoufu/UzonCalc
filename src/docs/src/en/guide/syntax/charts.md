---
title: Charts
icon: chart-simple
order: 8
---

## Chart Types

UzonCalc can insert several kinds of charts into reports:

- `Img()`: insert an image
- `Table()`: insert a table
- `EChart()`: insert an interactive ECharts chart
- `Plot()` or Matplotlib: insert a static plot

Interactive charts are best for browser viewing. Static Matplotlib images are better for printing and export.

## Images

```python
Img(
    "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
    alt="UzonCalc run result",
)
```

Images participate in automatic numbering, and their placeholders can be referenced later in the body text.

## ECharts

`EChart()` accepts ECharts `options`:

```python
EChart(
    {
        "title": {"text": "Stacked Area Chart"},
        "tooltip": {"trigger": "axis"},
        "xAxis": [{"type": "category", "data": ["Mon", "Tue", "Wed"]}],
        "yAxis": [{"type": "value"}],
        "series": [
            {
                "name": "Email",
                "type": "line",
                "data": [120, 132, 101],
            }
        ],
    }
)
```

See the [ECharts examples](https://echarts.apache.org/examples/en/index.html) for more configuration options.

## ECharts GL

Use `use_gl=True` for 3D charts:

```python
ROOT_PATH = "https://oss.uzoncloud.com:2234/public/files/images"

EChart(
    {
        "backgroundColor": "#000",
        "globe": {
            "baseTexture": ROOT_PATH + "/earth.jpg",
            "heightTexture": ROOT_PATH + "/bathymetry_bw_composite_4k.jpg",
            "displacementScale": 0.1,
            "shading": "lambert",
        },
        "series": [],
    },
    use_gl=True,
    caption="3D Earth example",
)
```

## Matplotlib

Matplotlib charts are emitted as static images and are suitable for printing:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [2, 4, 6])
Plot(fig, caption="Line chart")
```
