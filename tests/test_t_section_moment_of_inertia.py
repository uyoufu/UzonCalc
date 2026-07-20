import importlib.util
import json
from pathlib import Path

from uzoncalc import run_sync


def _load_t_section_module():
    """加载中文 T 形截面惯性矩示例模块。"""
    module_path = Path("examples/zh/T_section_moment_of_inertia.py")
    spec = importlib.util.spec_from_file_location("t_section_moment", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extract_first_echart_option(html: str) -> dict:
    """从示例 HTML 中提取首个 ECharts setOption 配置。"""
    marker = "chart.setOption("
    option_start = html.index(marker) + len(marker)
    option_end = html.index(");", option_start)
    return json.loads(html[option_start:option_end])


def test_t_section_diagram_draws_rectangles_and_neutral_axis():
    """T 形截面示意图应绘制翼缘、腹板和中性轴。"""
    module = _load_t_section_module()

    ctx = run_sync(module.sheet)
    option = _extract_first_echart_option(ctx.html_content())
    series = option["series"]
    mark_area_series = next(item for item in series if "markArea" in item)
    outline_series = next(item for item in series if item.get("name") == "T 形截面轮廓")
    neutral_axis_series = next(item for item in series if "markLine" in item)

    assert "markLine" not in option
    assert mark_area_series["markArea"]["data"] == [
        [
            {"name": "翼缘", "coord": [0, 200]},
            {"coord": [300, 250]},
        ],
        [
            {"name": "腹板", "coord": [100, 0]},
            {"coord": [200, 200]},
        ],
    ]
    assert outline_series["data"] == [
        [0, 200],
        [0, 250],
        [300, 250],
        [300, 200],
        [200, 200],
        [200, 0],
        [100, 0],
        [100, 200],
        [0, 200],
    ]
    assert neutral_axis_series["markLine"]["data"] == [
        [
            {"name": "中性轴", "coord": [0, 153.57142857142858]},
            {"coord": [300, 153.57142857142858]},
        ]
    ]
