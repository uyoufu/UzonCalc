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

    enable_fstring_equation()
    f"翼缘宽度：{(b_f := 300 * unit.mm)}"

    f"翼缘厚度：{(h_f := 50 * unit.mm)}"

    H3("腹板参数")

    f"腹板宽度：{(b_w := 100 * unit.mm)}"

    f"腹板高度：{(h_w := 200 * unit.mm)}"
    disable_fstring_equation()

    "截面总高度："
    h_total = h_f + h_w

    H2("截面几何特征")

    H3("面积计算")

    "翼缘面积："
    A_f = b_f * h_f

    "腹板面积："
    A_w = b_w * h_w

    "总面积："
    A_total = A_f + A_w

    H3("中立轴位置")

    """
    以截面底部为参考轴（y=0），计算各部分的重心到参考轴的距离。
    """

    "翼缘重心高度（以底部计）："
    y_f = h_w + h_f / 2

    "腹板重心高度（以底部计）："
    y_w = h_w / 2

    "中立轴位置（以底部计）："
    y_c = (A_f * y_f + A_w * y_w) / A_total

    H2("惯性矩计算")

    H3("关于中立轴的惯性矩")

    """
    采用平行轴定理计算各部分关于中立轴的惯性矩。
    公式：I_c = I_g + A * d²
    其中 I_g 为自身惯性矩，A 为面积，d 为重心到中立轴的距离。
    """

    "翼缘自身惯性矩（关于其重心轴）："
    I_f_self = b_f * h_f**3 / 12

    "翼缘到中立轴的距离："
    d_f = abs(y_f - y_c)

    "翼缘关于中立轴的惯性矩："
    I_f = I_f_self + A_f * d_f**2

    Br()

    "腹板自身惯性矩（关于其重心轴）："
    I_w_self = b_w * h_w**3 / 12

    "腹板到中立轴的距离："
    d_w = abs(y_w - y_c)

    "腹板关于中立轴的惯性矩："
    I_w = I_w_self + A_w * d_w**2

    "T 形截面总惯性矩（关于中立轴）："
    I_total = I_f + I_w

    H3("截面抵抗矩")

    "上（翼缘）侧极端纤维到中立轴的距离："
    e_top = h_total - y_c

    "下（腹板底部）侧极端纤维到中立轴的距离："
    e_bottom = y_c

    "上侧截面抵抗矩："
    W_top = I_total / e_top

    "下侧截面抵抗矩："
    W_bottom = I_total / e_bottom

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
            [
                "高度 (mm)",
                f"{h_f.magnitude:.0f}",
                f"{h_w.magnitude:.0f}",
                f"{h_total.magnitude:.0f}",
            ],
            [
                "面积 (mm²)",
                f"{A_f.magnitude:.0f}",
                f"{A_w.magnitude:.0f}",
                f"{A_total.magnitude:.0f}",
            ],
            [
                "自身惯性矩 (mm⁴)",
                f"{I_f_self.magnitude:.2e}",
                f"{I_w_self.magnitude:.2e}",
                "-",
            ],
            ["到中立轴距离 (mm)", f"{d_f.magnitude:.2f}", f"{d_w.magnitude:.2f}", "-"],
            [
                "关于中立轴惯性矩 (mm⁴)",
                f"{I_f.magnitude:.2e}",
                f"{I_w.magnitude:.2e}",
                f"{I_total.magnitude:.2e}",
            ],
        ],
        title="T 形截面性质统计表",
    )

    Br()

    H2("计算结果汇总")

    H3("几何特征")

    inline()
    "截面总面积 A = "
    A_total
    end_inline()

    inline()
    "中立轴位置（以底部计）y_c = "
    y_c
    end_inline()

    H3("惯性矩")

    inline()
    "截面惯性矩 I_c = "
    I_total
    end_inline()

    H3("截面抵抗矩")

    inline()
    "上侧抵抗矩 W_top = "
    W_top
    end_inline()

    inline()
    "下侧抵抗矩 W_bottom = "
    W_bottom
    end_inline()

    Br()

    H2("截面示意图")

    """
    下方用 ECharts 绘制 T 形截面的几何示意图，标注了关键尺寸。
    """

    # 计算用于绘图的数值
    hide()
    b_f_val = b_f.to(unit.mm).magnitude
    h_f_val = h_f.to(unit.mm).magnitude
    b_w_val = b_w.to(unit.mm).magnitude
    h_w_val = h_w.to(unit.mm).magnitude
    y_c_val = y_c.to(unit.mm).magnitude
    web_left = (b_f_val - b_w_val) / 2
    web_right = web_left + b_w_val
    show()
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
                    "type": "line",
                    "data": [],
                    "silent": True,
                    # markArea 负责填充两个矩形区域，避免透明散点导致示意图不可见。
                    "markArea": {
                        "silent": True,
                        "itemStyle": {
                            "color": "rgba(70, 130, 180, 0.22)",
                            "borderColor": "#2f6f9f",
                            "borderWidth": 1,
                        },
                        "data": [
                            [
                                {"name": "翼缘", "coord": [0, h_w_val]},
                                {"coord": [b_f_val, h_w_val + h_f_val]},
                            ],
                            [
                                {"name": "腹板", "coord": [web_left, 0]},
                                {"coord": [web_right, h_w_val]},
                            ],
                        ],
                    },
                },
                {
                    "name": "T 形截面轮廓",
                    "type": "line",
                    "symbol": "none",
                    "lineStyle": {"color": "#1f4e79", "width": 2},
                    "data": [
                        [0, h_w_val],
                        [0, h_w_val + h_f_val],
                        [b_f_val, h_w_val + h_f_val],
                        [b_f_val, h_w_val],
                        [web_right, h_w_val],
                        [web_right, 0],
                        [web_left, 0],
                        [web_left, h_w_val],
                        [0, h_w_val],
                    ],
                },
                {
                    "type": "line",
                    "data": [],
                    "markLine": {
                        "symbol": "none",
                        "label": {
                            "show": True,
                            "formatter": "中性轴",
                            "position": "insideEndTop",
                        },
                        "lineStyle": {"color": "red", "type": "dashed", "width": 2},
                        "data": [
                            [
                                {"name": "中性轴", "coord": [0, y_c_val]},
                                {"coord": [b_f_val, y_c_val]},
                            ]
                        ],
                    },
                },
            ],
        }
    )

    Br()

    H2("计算说明")

    Markdown("""
本计算采用平行轴定理计算 T 形截面的惯性矩。具体步骤为：
1. 将 T 形截面分解为两个矩形部分：翼缘和腹板；
2. 明确各部分的几何参数（宽度和高度）；
3. 选择参考轴（本例选择截面底部作为参考）计算各部分的重心位置；
4. 计算整个截面的重心位置（即中立轴位置）；
5. 利用平行轴定理，计算各部分关于中立轴的惯性矩；
6. 将各部分的惯性矩相加得到总的惯性矩；
7. 根据中立轴位置和极端纤维距离计算截面抵抗矩。
             
这种方法适用于所有由矩形组成的截面形状。
    """)


if __name__ == "__main__":
    view(sheet)
