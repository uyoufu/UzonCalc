from uzoncalc import *
from uzoncalc.extension.echarts import EChart, Javascript


@uzon_calc()
async def sheet():
    H1("echarts 图表示例")

    H2("ECharts 示例")

    "可以使用 echarts 库创建丰富的交互式图表, 更多内容请参考官方文档和示例: https://echarts.apache.org/examples/zh/index.html#chart-type-line"

    "示例中的 options 参数参考：https://echarts.apache.org/examples/zh/editor.html?c=area-stack"

    # 参数参考：https://echarts.apache.org/examples/zh/editor.html?c=area-stack
    EChart(
        {
            "title": {"text": "Stacked Area Chart"},
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "cross",
                    "label": {"backgroundColor": "#6a7985"},
                },
            },
            "legend": {
                "data": [
                    "Email",
                    "Union Ads",
                    "Video Ads",
                    "Direct",
                    "Search Engine",
                ]
            },
            "toolbox": {"feature": {"saveAsImage": {}}},
            "xAxis": [
                {
                    "type": "category",
                    "boundaryGap": False,
                    "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                }
            ],
            "yAxis": [{"type": "value"}],
            "series": [
                {
                    "name": "Email",
                    "type": "line",
                    "stack": "Total",
                    "areaStyle": {},
                    "emphasis": {"focus": "series"},
                    "data": [120, 132, 101, 134, 90, 230, 210],
                },
                {
                    "name": "Union Ads",
                    "type": "line",
                    "stack": "Total",
                    "areaStyle": {},
                    "emphasis": {"focus": "series"},
                    "data": [220, 182, 191, 234, 290, 330, 310],
                },
                {
                    "name": "Video Ads",
                    "type": "line",
                    "stack": "Total",
                    "areaStyle": {},
                    "emphasis": {"focus": "series"},
                    "data": [150, 232, 201, 154, 190, 330, 410],
                },
                {
                    "name": "Direct",
                    "type": "line",
                    "stack": "Total",
                    "areaStyle": {},
                    "emphasis": {"focus": "series"},
                    "data": [320, 332, 301, 334, 390, 330, 320],
                },
                {
                    "name": "Search Engine",
                    "type": "line",
                    "stack": "Total",
                    "label": {"show": True, "position": "top"},
                    "areaStyle": {},
                    "emphasis": {"focus": "series"},
                    "data": [820, 932, 901, 934, 1290, 1330, 1320],
                },
            ],
        }
    )

    H2("ECharts 3D 示例")

    "可以使用 ECharts GL 创建 3D 图表。可以使用鼠标旋转、缩放图表以查看不同的角度和细节。"

    # 参数参考：https://echarts.apache.org/examples/zh/editor.html?c=simple-surface&gl=1
    EChart(
        {
            "tooltip": {},
            "backgroundColor": "#fff",
            "visualMap": {
                "show": False,
                "dimension": 2,
                "min": -1,
                "max": 1,
                "inRange": {
                    "color": [
                        "#4575b4",
                        "#74add1",
                        "#abd9e9",
                        "#e0f3f8",
                        "#ffffbf",
                        "#fee090",
                        "#fdae61",
                        "#f46d43",
                    ]
                },
            },
            "xAxis3D": {"type": "value"},
            "yAxis3D": {"type": "value"},
            "zAxis3D": {"type": "value"},
            "grid3D": {"viewControl": {}},
            "series": [
                {
                    "type": "surface",
                    "wireframe": {},
                    "equation": {
                        "x": {"step": 0.05},
                        "y": {"step": 0.05},
                        "z": Javascript("""
function (x, y) {
  if (Math.abs(x) < 0.1 && Math.abs(y) < 0.1) {
    return '-';
  }
  return Math.sin(x * Math.PI) * Math.sin(y * Math.PI);
}
"""),
                    },
                }
            ],
        },
        use_gl=True,
    )


if __name__ == "__main__":
    view(sheet)
