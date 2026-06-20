---
title: 图表
icon: chart-simple
order: 8
---

## 图表类型

UzonCalc 可以在计算书中插入多种图表：

- `Img()`：插入图片
- `Table()`：插入表格
- `EChart()`：插入 ECharts 交互式图表
- `Plot()` 或 Matplotlib：插入静态绘图结果

交互式图表适合浏览器查看，Matplotlib 静态图片更适合打印和导出。

## 图片

```python
Img(
    "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
    alt="UzonCalc 运行结果",
)
```

图片会参与自动编号，也可以在后续正文中引用编号占位符。

## ECharts

`EChart()` 接收 ECharts 的 `options` 配置：

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

更多配置可参考 [ECharts 示例](https://echarts.apache.org/examples/zh/index.html)。

## ECharts GL

需要 3D 图表时，可以启用 `use_gl=True`：

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
    caption="3D 地球示例",
)
```

## Matplotlib

Matplotlib 图表会以静态图片形式输出，适合打印：

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [2, 4, 6])
Plot(fig, caption="折线图")
```
