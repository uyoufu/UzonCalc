from uzoncalc import *
from uzoncalc.extension.echarts import EChart, Javascript
from uzoncalc.extension.js import Js, js


@uzon_calc()
async def sheet():
    H1("图表示例")

    toc("目录")

    H2("2D 示例")

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

    H2("折柱混合图")

    """参考: https://echarts.apache.org/examples/zh/editor.html?c=mix-line-bar"""

    Js(
        """
var chartDom = document.getElementById('echarts-container-100');
var myChart = echarts.init(chartDom);
var option;

option = {
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'cross',
      crossStyle: {
        color: '#999'
      }
    }
  },
  toolbox: {
    feature: {
      dataView: { show: true, readOnly: false },
      magicType: { show: true, type: ['line', 'bar'] },
      restore: { show: true },
      saveAsImage: { show: true }
    }
  },
  legend: {
    data: ['Evaporation', 'Precipitation', 'Temperature']
  },
  xAxis: [
    {
      type: 'category',
      data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      axisPointer: {
        type: 'shadow'
      }
    }
  ],
  yAxis: [
    {
      type: 'value',
      name: 'Precipitation',
      min: 0,
      max: 250,
      interval: 50,
      axisLabel: {
        formatter: '{value} ml'
      }
    },
    {
      type: 'value',
      name: 'Temperature',
      min: 0,
      max: 25,
      interval: 5,
      axisLabel: {
        formatter: '{value} °C'
      }
    }
  ],
  series: [
    {
      name: 'Evaporation',
      type: 'bar',
      tooltip: {
        valueFormatter: function (value) {
          return value + ' ml';
        }
      },
      data: [
        2.0, 4.9, 7.0, 23.2, 25.6, 76.7, 135.6, 162.2, 32.6, 20.0, 6.4, 3.3
      ]
    },
    {
      name: 'Precipitation',
      type: 'bar',
      tooltip: {
        valueFormatter: function (value) {
          return value + ' ml';
        }
      },
      data: [
        2.6, 5.9, 9.0, 26.4, 28.7, 70.7, 175.6, 182.2, 48.7, 18.8, 6.0, 2.3
      ]
    },
    {
      name: 'Temperature',
      type: 'line',
      yAxisIndex: 1,
      tooltip: {
        valueFormatter: function (value) {
          return value + ' °C';
        }
      },
      data: [2.0, 2.2, 3.3, 4.5, 6.3, 10.2, 20.3, 23.4, 23.0, 16.5, 12.0, 6.2]
    }
  ]
};

option && myChart.setOption(option);
""",
        "break-inside-avoid",
        props=Props(
            id="echarts-container-100",
            style={
                "width": "100%",
                "height": "400px",
            },
        ),
    )

    H2("ECharts Two Value-Axes in Polar")

    from math import sin, cos, pi as PI

    hide()
    data = []
    for i in range(360):
        t = (i / 180) * PI
        r = sin(2 * t) * cos(2 * t)
        data.append([r, i])
    show()

    EChart(
        {
            "title": {"text": "Two Value-Axes in Polar"},
            "legend": {"data": ["line"]},
            "polar": {"center": ["50%", "54%"]},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
            "angleAxis": {"type": "value", "startAngle": 0},
            "radiusAxis": {"min": 0},
            "series": [
                {
                    "coordinateSystem": "polar",
                    "name": "line",
                    "type": "line",
                    "showSymbol": False,
                    "data": data,
                }
            ],
            "animationDuration": 2000,
        }
    )

    H2("3D地球 示例")

    "参考：https://echarts.apache.org/examples/zh/editor.html?c=globe-layers&gl=1"

    hide()
    ROOT_PATH = "https://oss.uzoncloud.com:2234/public/files/images"
    show()

    EChart(
        {
            "backgroundColor": "#000",
            "globe": {
                "baseTexture": ROOT_PATH + "/earth.jpg",
                "heightTexture": ROOT_PATH + "/bathymetry_bw_composite_4k.jpg",
                "displacementScale": 0.1,
                "shading": "lambert",
                "environment": ROOT_PATH + "/starfield.jpg",
                "light": {"ambient": {"intensity": 0.1}, "main": {"intensity": 1.5}},
                "layers": [
                    {
                        "type": "blend",
                        "blendTo": "emission",
                        "texture": ROOT_PATH + "/night.jpg",
                    },
                    {
                        "type": "overlay",
                        "texture": ROOT_PATH + "/clouds.png",
                        "shading": "lambert",
                        "distance": 5,
                    },
                ],
            },
            "series": [],
        },
        use_gl=True,
    )

    H2("3D Mesh 示例")

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
