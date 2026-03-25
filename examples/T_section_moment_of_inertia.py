from pathlib import Path
import sys
import numpy as np

# 使用 pip 包时, 不需要该行；仅在从 core 目录运行该脚本时需要
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uzoncalc import *
from uzoncalc.extension.echarts import EChart


@uzon_calc()
async def sheet():
    doc_title("T 形截面惯性矩计算")
    page_size("A4")

    H1("T 形截面惯性矩计算")

    Info("本文档计算 T 形截面关于其中立轴的惯性矩。")

    toc("目录")

    H2("截面基本参数")

    """
    T 形截面由两个矩形部分组成：翼缘（上部分）和腹板（下部分）。
    下面分别定义两部分的几何参数。
    """

    H3("翼缘参数")

    "翼缘宽度："
    b_f = 300 * unit.millimeter
    alias("b_f", "翼缘宽度 b_f")

    "翼缘厚度："
    h_f = 50 * unit.millimeter
    alias("h_f", "翼缘厚度 h_f")

    H3("腹板参数")

    "腹板宽度："
    b_w = 100 * unit.millimeter
    alias("b_w", "腹板宽度 b_w")

    "腹板高度："
    h_w = 200 * unit.millimeter
    alias("h_w", "腹板高度 h_w")

    "截面总高度："
    h_total = h_f + h_w
    alias("h_total", "截面总高度 h")

    Br()

    H2("截面几何特征")

    H3("面积计算")

    "翼缘面积："
    A_f = b_f * h_f
    alias("A_f", "翼缘面积 A_f")

    "腹板面积："
    A_w = b_w * h_w
    alias("A_w", "腹板面积 A_w")

    "总面积："
    A_total = A_f + A_w
    alias("A_total", "总面积 A")

    H3("中立轴位置")

    """
    以截面底部为参考轴（y=0），计算各部分的重心到参考轴的距离。
    """

    "翼缘重心高度（以底部计）："
    y_f = h_w + h_f / 2
    alias("y_f", "翼缘重心高度 y_f")

    "腹板重心高度（以底部计）："
    y_w = h_w / 2
    alias("y_w", "腹板重心高度 y_w")

    "中立轴位置（以底部计）："
    y_c = (A_f * y_f + A_w * y_w) / A_total
    alias("y_c", "中立轴位置 y_c")

    Br()

    H2("惯性矩计算")

    H3("关于中立轴的惯性矩")

    """
    采用平行轴定理计算各部分关于中立轴的惯性矩。
    公式：I_c = I_g + A * d²
    其中 I_g 为自身惯性矩，A 为面积，d 为重心到中立轴的距离。
    """

    "翼缘自身惯性矩（关于其重心轴）："
    I_f_self = b_f * h_f**3 / 12
    alias("I_f_self", "翼缘自身惯性矩 I_f,g")

    "翼缘到中立轴的距离："
    d_f = abs(y_f - y_c)
    alias("d_f", "翼缘到中立轴距离 d_f")

    "翼缘关于中立轴的惯性矩："
    I_f = I_f_self + A_f * d_f**2
    alias("I_f", "翼缘惯性矩 I_f")

    Br()

    "腹板自身惯性矩（关于其重心轴）："
    I_w_self = b_w * h_w**3 / 12
    alias("I_w_self", "腹板自身惯性矩 I_w,g")

    "腹板到中立轴的距离："
    d_w = abs(y_w - y_c)
    alias("d_w", "腹板到中立轴距离 d_w")

    "腹板关于中立轴的惯性矩："
    I_w = I_w_self + A_w * d_w**2
    alias("I_w", "腹板惯性矩 I_w")

    Br()

    "T 形截面总惯性矩（关于中立轴）："
    I_total = I_f + I_w
    alias("I_total", "总惯性矩 I_c")

    Br()

    H3("截面抵抗矩")

    "上（翼缘）侧极端纤维到中立轴的距离："
    e_top = h_total - y_c
    alias("e_top", "上侧距离 e_top")

    "下（腹板底部）侧极端纤维到中立轴的距离："
    e_bottom = y_c
    alias("e_bottom", "下侧距离 e_bottom")

    "上侧截面抵抗矩："
    W_top = I_total / e_top
    alias("W_top", "上侧抵抗矩 W_top")

    "下侧截面抵抗矩："
    W_bottom = I_total / e_bottom
    alias("W_bottom", "下侧抵抗矩 W_bottom")

    Br()

    H2("截面性质对比表")

    Table(
        [
            [
                th("性质", rowspan=2),
                th("翼缘部分", rowspan=1),
                th("腹板部分", rowspan=1),
                th("总计", rowspan=1),
            ],
        ],
        [
            ["宽度 (mm)", f"{b_f.magnitude:.0f}", f"{b_w.magnitude:.0f}", "-"],
            ["高度 (mm)", f"{h_f.magnitude:.0f}", f"{h_w.magnitude:.0f}", f"{h_total.magnitude:.0f}"],
            ["面积 (mm²)", f"{A_f.magnitude:.0f}", f"{A_w.magnitude:.0f}", f"{A_total.magnitude:.0f}"],
            ["自身惯性矩 (mm⁴)", f"{I_f_self.magnitude:.2e}", f"{I_w_self.magnitude:.2e}", "-"],
            ["到中立轴距离 (mm)", f"{d_f.magnitude:.2f}", f"{d_w.magnitude:.2f}", "-"],
            ["关于中立轴惯性矩 (mm⁴)", f"{I_f.magnitude:.2e}", f"{I_w.magnitude:.2e}", f"{I_total.magnitude:.2e}"],
        ],
        title="T 形截面性质统计表",
    )

    Br()

    H2("计算结果汇总")

    H3("几何特征")

    inline()
    "截面总面积 A = "
    A_total
    endline()

    inline()
    "中立轴位置（以底部计）y_c = "
    y_c
    endline()

    H3("惯性矩")

    inline()
    "截面惯性矩 I_c = "
    I_total
    endline()

    H3("截面抵抗矩")

    inline()
    "上侧抵抗矩 W_top = "
    W_top
    endline()

    inline()
    "下侧抵抗矩 W_bottom = "
    W_bottom
    endline()

    Br()

    H2("截面示意图")

    """
    下方用 ECharts 绘制 T 形截面的几何示意图，标注了关键尺寸。
    """

    # 计算用于绘图的数值
    b_f_val = b_f.to(unit.millimeter).magnitude
    h_f_val = h_f.to(unit.millimeter).magnitude
    b_w_val = b_w.to(unit.millimeter).magnitude
    h_w_val = h_w.to(unit.millimeter).magnitude
    y_c_val = y_c.to(unit.millimeter).magnitude

    EChart(
        {
            "title": {"text": "T 形截面几何示意图"},
            "tooltip": {"trigger": "axis"},
            "grid": {"left": "10%", "right": "10%", "bottom": "10%", "top": "10%"},
            "xAxis": {
                "type": "value",
                "min": -50,
                "max": max(b_f_val, b_w_val) + 50,
                "name": "宽度 (mm)",
            },
            "yAxis": {
                "type": "value",
                "min": -50,
                "max": h_f_val + h_w_val + 50,
                "name": "高度 (mm)",
            },
            "series": [
                {
                    "type": "scatter",
                    "symbolSize": 8,
                    "data": [
                        [(b_f_val - b_w_val) / 2, h_w_val],  # 翼缘左下
                        [(b_f_val - b_w_val) / 2 + b_w_val, h_w_val],  # 翼缘右下
                        [(b_f_val - b_w_val) / 2 + b_w_val, h_w_val + h_f_val],  # 翼缘右上
                        [(b_f_val - b_w_val) / 2, h_w_val + h_f_val],  # 翼缘左上
                        [0, 0],  # 腹板左下
                        [b_w_val, 0],  # 腹板右下
                        [b_w_val, h_w_val],  # 腹板右上
                        [0, h_w_val],  # 腹板左上
                        [b_f_val / 2, y_c_val],  # 中立轴位置
                    ],
                    "itemStyle": {"color": "rgba(0, 0, 0, 0)"},
                }
            ],
            "markLine": {
                "data": [
                    {"yAxis": y_c_val, "name": "中立轴", "lineStyle": {"color": "red", "type": "dashed"}},
                ]
            },
        }
    )

    Br()

    H2("计算说明")

    """
    本计算采用平行轴定理计算 T 形截面的惯性矩。具体步骤为：

    1. 将 T 形截面分解为两个矩形部分：翼缘和腹板；

    2. 明确各部分的几何参数（宽度和高度）；

    3. 选择参考轴（本例选择截面底部作为参考）计算各部分的重心位置；

    4. 计算整个截面的重心位置（即中立轴位置）；

    5. 利用平行轴定理，计算各部分关于中立轴的惯性矩；

    6. 将各部分的惯性矩相加得到总的惯性矩；

    7. 根据中立轴位置和极端纤维距离计算截面抵抗矩。

    这种方法适用于所有由矩形组成的截面形状。
    """

    save("../output/T_section_moment_of_inertia.html")


if __name__ == "__main__":
    ctx = run_sync(sheet)
