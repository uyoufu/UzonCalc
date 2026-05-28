from uuid import uuid4

from ..context_utils.doc import head
from ..globals import get_current_instance
import itertools
import json


class Javascript:
    """Marker for raw JavaScript snippets embedded into serialized chart options."""

    def __init__(self, code: str):
        self.code = code


def use_echarts():
    """
    添加 ECharts 支持
    """

    head(
        "script",
        {"src": "https://echarts.apache.org/zh/js/vendors/echarts/dist/echarts.min.js"},
    )


def use_echarts_gl():
    """
    添加 ECharts GL 支持，用于 3D 图表
    """

    head(
        "script",
        {
            "src": "https://echarts.apache.org/zh/js/vendors/echarts-gl/dist/echarts-gl.min.js"
        },
    )


def echart(
    options: dict,
    width: str = "100%",
    height: str = "400px",
    use_gl: bool = False,
) -> str:
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

    if use_gl:
        use_echarts_gl()

    raw_js_placeholders: dict[str, str] = {}
    # 从 1 开始的计数器，用于生成唯一的占位符
    raw_js_counter = itertools.count(1)

    def encode_default(value):
        if isinstance(value, Javascript):
            token = f"__UZONCALC_RAW_JS_{next(raw_js_counter)}__"
            raw_js_placeholders[json.dumps(token)] = value.code
            return token

        raise TypeError(
            f"Object of type {type(value).__name__} is not JSON serializable"
        )

    # options_json 是字符串，里面有 js 代码应不再包含引号
    options_json = json.dumps(options, default=encode_default)

    # 替换占位符为原始 JavaScript 代码
    for token_json, raw_js in raw_js_placeholders.items():
        options_json = options_json.replace(token_json, raw_js)

    # 随机唯一 ID，确保多个图表不会冲突
    container_id = f"echart-container-{uuid4().hex[:8]}"

    return f"""
<figure id="{container_id}" style="width: {width}; height: {height};" class="break-inside-avoid">
    <script>
        (function() {{
            const dom = document.getElementById("{container_id}");
            let chart = null;
            let resizeObserver = null;

            function initChartWhenReady() {{
                if (!dom || !window.echarts) {{
                    return;
                }}

                if (dom.clientWidth === 0 || dom.clientHeight === 0) {{
                    requestAnimationFrame(initChartWhenReady);
                    return;
                }}

                if (!chart) {{
                    chart = echarts.init(dom);
                }}

                chart.setOption({options_json});

                if (typeof ResizeObserver !== 'undefined' && !resizeObserver) {{
                    resizeObserver = new ResizeObserver(function () {{
                        if (chart) {{
                            chart.resize();
                        }}
                    }});
                    resizeObserver.observe(dom);
                }}
            }}

            initChartWhenReady();
        }})();
    </script>
</figure>
"""


def EChart(
    options: dict,
    width: str = "100%",
    height: str = "400px",
    use_gl: bool = False,
):
    """
    生成 ECharts 图表的 HTML 代码，作为新版本的接口

    Args:
        options: ECharts 配置项，字典形式
        width: 图表宽度，默认为 "100%"
        height: 图表高度，默认为 "400px"

    Returns:
        包含 ECharts 图表的 HTML 字符串
    """
    current_instance = get_current_instance()
    current_instance.append_content(echart(options, width, height, use_gl=use_gl))
