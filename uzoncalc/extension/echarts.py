from ..context_utils.doc import head
from ..context_utils.elements import Div
import json


def use_echarts():
    """
    添加 ECharts 支持
    """

    head(
        "script",
        {
            "src": "https://cdnjs.cloudflare.com/ajax/libs/echarts/6.0.0/echarts.min.js",
            "integrity": "sha512-4/g9GAdOdTpUP2mKClpKsEzaK7FQNgMjq+No0rX8XZlfrCGtbi4r+T/p5fnacsEC3zIAmHKLJUL7sh3/yVA4OQ==",
            "crossorigin": "anonymous",
            "referrerpolicy": "no-referrer",
        },
    )


def echart(options: dict, width: str = "100%", height: str = "400px") -> str:
    """
    生成 ECharts 图表的 HTML 代码

    Args:
        options: ECharts 配置项，字典形式
        width: 图表宽度，默认为 "100%"
        height: 图表高度，默认为 "400px"

    Returns:
        包含 ECharts 图表的 HTML 字符串
    """

    use_echarts()  # 确保 ECharts 脚本已添加到页面头部

    options_json = json.dumps(options)
    return f"""
<div style="width: {width}; height: {height};">
  <script>var chart = echarts.init(document.currentScript.parentElement); chart.setOption({options_json});</script>
</div>
"""


def EChart(options: dict, width: str = "100%", height: str = "400px"):
    """
    生成 ECharts 图表的 HTML 代码，作为新版本的接口

    Args:
        options: ECharts 配置项，字典形式
        width: 图表宽度，默认为 "100%"
        height: 图表高度，默认为 "400px"

    Returns:
        包含 ECharts 图表的 HTML 字符串
    """
    Div(echart(options, width, height))
