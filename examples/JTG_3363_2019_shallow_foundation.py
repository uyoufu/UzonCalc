from dataclasses import dataclass
from pathlib import Path
import math
import sys

# 使用 pip 包时, 不需要该行；仅在从仓库目录运行该脚本时需要
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uzoncalc import *
from uzoncalc.extension.echarts import EChart


@dataclass(slots=True)
class RectangleSection:
    """矩形基础平面截面计算器。"""

    width: any
    height: any

    def outline_points(self) -> list[tuple[float, float]]:
        """返回用于绘图的闭合轮廓点。"""
        width_m = self.width.to(unit.meter).magnitude
        height_m = self.height.to(unit.meter).magnitude
        return [
            (0.0, 0.0),
            (width_m, 0.0),
            (width_m, height_m),
            (0.0, height_m),
            (0.0, 0.0),
        ]

    @property
    def area(self):
        return self.width * self.height

    @property
    def centroid_x(self):
        return self.width / 2

    @property
    def centroid_y(self):
        return self.height / 2

    @property
    def inertia_x(self):
        return self.width * self.height**3 / 12

    @property
    def inertia_y(self):
        return self.height * self.width**3 / 12

    @property
    def section_modulus_x(self):
        return self.inertia_x / (self.height / 2)

    @property
    def section_modulus_y(self):
        return self.inertia_y / (self.width / 2)

    @property
    def kern_x(self):
        return self.width / 6

    @property
    def kern_y(self):
        return self.height / 6


@dataclass(slots=True)
class LoadCase:
    """基底反力工况输入。"""

    case_id: str
    Nz: any
    Mx: any
    My: any
    Hx: any
    Hy: any
    gamma_R: float
    required_ecc_sf: float
    required_overturn_sf: float
    required_slide_sf: float


@dataclass(slots=True)
class CaseResult:
    """单工况计算结果。"""

    load_case: LoadCase
    ex: any
    ey: any
    q_avg: any
    q_max: any
    q_min: any
    bearing_sf: float
    average_sf: float
    actual_ecc_sf: float
    required_ecc_sf: float
    overturn_sf: float
    slide_sf: float
    resultant_x: float
    resultant_y: float


def build_rectangle_section(width, height) -> RectangleSection:
    """构造矩形截面，后续扩展其他截面时可复用该入口。"""
    return RectangleSection(width=width, height=height)


def get_corner_pressures(section: RectangleSection, load_case: LoadCase):
    """计算矩形截面四角的基底压应力。"""
    x_edge = section.width / 2
    y_edge = section.height / 2
    q_avg = load_case.Nz / section.area

    pressures = {
        "左下角": q_avg - load_case.Mx * y_edge / section.inertia_x - load_case.My * x_edge / section.inertia_y,
        "右下角": q_avg - load_case.Mx * y_edge / section.inertia_x + load_case.My * x_edge / section.inertia_y,
        "右上角": q_avg + load_case.Mx * y_edge / section.inertia_x + load_case.My * x_edge / section.inertia_y,
        "左上角": q_avg + load_case.Mx * y_edge / section.inertia_x - load_case.My * x_edge / section.inertia_y,
    }
    return q_avg, pressures


def calculate_eccentric_safety(section: RectangleSection, ex, ey) -> float:
    """按矩形截面核心范围计算偏心距安全系数。"""
    ex_abs = abs(ex.to(unit.meter).magnitude)
    ey_abs = abs(ey.to(unit.meter).magnitude)
    limit_x = section.kern_x.to(unit.meter).magnitude
    limit_y = section.kern_y.to(unit.meter).magnitude

    factor_x = math.inf if ex_abs == 0 else limit_x / ex_abs
    factor_y = math.inf if ey_abs == 0 else limit_y / ey_abs
    return min(factor_x, factor_y)


def evaluate_load_case(section: RectangleSection, load_case: LoadCase, bearing_capacity):
    """执行单工况验算。"""
    q_avg, pressures = get_corner_pressures(section, load_case)
    q_max = max(pressures.values())
    q_min = min(pressures.values())
    ex = load_case.My / load_case.Nz
    ey = load_case.Mx / load_case.Nz
    actual_ecc_sf = calculate_eccentric_safety(section, ex, ey)

    q_max_kpa = q_max.to(unit.kilopascal).magnitude
    q_avg_kpa = q_avg.to(unit.kilopascal).magnitude
    bearing_capacity_kpa = bearing_capacity.to(unit.kilopascal).magnitude

    bearing_sf = math.inf if q_max_kpa <= 0 else load_case.gamma_R * bearing_capacity_kpa / q_max_kpa
    average_sf = math.inf if q_avg_kpa <= 0 else bearing_capacity_kpa / q_avg_kpa

    resultant_x = section.centroid_x.to(unit.meter).magnitude + ex.to(unit.meter).magnitude
    resultant_y = section.centroid_y.to(unit.meter).magnitude + ey.to(unit.meter).magnitude

    return CaseResult(
        load_case=load_case,
        ex=ex,
        ey=ey,
        q_avg=q_avg,
        q_max=q_max,
        q_min=q_min,
        bearing_sf=bearing_sf,
        average_sf=average_sf,
        actual_ecc_sf=actual_ecc_sf,
        required_ecc_sf=load_case.required_ecc_sf,
        overturn_sf=load_case.required_overturn_sf,
        slide_sf=load_case.required_slide_sf,
        resultant_x=resultant_x,
        resultant_y=resultant_y,
    )


def format_quantity(value, target_unit, digits: int = 2) -> str:
    """将带单位结果格式化为表格可读文本。"""
    converted = value.to(target_unit)
    return f"{converted.magnitude:.{digits}f} {converted.units:~P}"


def format_float(value: float, digits: int = 2) -> str:
    """格式化浮点数并兼容无穷大。"""
    if math.isinf(value):
        return "∞"
    return f"{value:.{digits}f}"


def build_section_chart(section: RectangleSection, results: list[CaseResult]):
    """构造矩形截面与荷载合力点示意图。"""
    width_m = section.width.to(unit.meter).magnitude
    height_m = section.height.to(unit.meter).magnitude
    cx = section.centroid_x.to(unit.meter).magnitude
    cy = section.centroid_y.to(unit.meter).magnitude
    kern_half_x = section.kern_x.to(unit.meter).magnitude
    kern_half_y = section.kern_y.to(unit.meter).magnitude
    outline = [[x, y] for x, y in section.outline_points()]
    kernel = [
        [cx - kern_half_x, cy - kern_half_y],
        [cx + kern_half_x, cy - kern_half_y],
        [cx + kern_half_x, cy + kern_half_y],
        [cx - kern_half_x, cy + kern_half_y],
        [cx - kern_half_x, cy - kern_half_y],
    ]
    resultant_points = [
        {
            "value": [result.resultant_x, result.resultant_y],
            "name": f"工况{result.load_case.case_id}",
        }
        for result in results
    ]

    return {
        "title": {"text": "矩形基础平面截面示意图"},
        "tooltip": {
            "trigger": "item",
            "formatter": "function(params){return params.name || '';}",
        },
        "legend": {"top": 24, "data": ["基础轮廓", "核心区", "形心", "荷载合力点"]},
        "xAxis": {
            "type": "value",
            "name": "x / m",
            "min": -0.2,
            "max": width_m + 0.2,
        },
        "yAxis": {
            "type": "value",
            "name": "y / m",
            "min": -0.2,
            "max": height_m + 0.2,
        },
        "series": [
            {
                "name": "基础轮廓",
                "type": "line",
                "data": outline,
                "symbol": "none",
                "lineStyle": {"width": 3, "color": "#1f2937"},
            },
            {
                "name": "核心区",
                "type": "line",
                "data": kernel,
                "symbol": "none",
                "lineStyle": {"width": 2, "type": "dashed", "color": "#ea580c"},
            },
            {
                "name": "形心",
                "type": "scatter",
                "data": [[cx, cy]],
                "symbolSize": 12,
                "itemStyle": {"color": "#dc2626"},
            },
            {
                "name": "荷载合力点",
                "type": "scatter",
                "data": resultant_points,
                "symbolSize": 14,
                "label": {"show": True, "position": "top", "formatter": "{b}"},
                "itemStyle": {"color": "#2563eb"},
            },
        ],
    }


def build_safety_chart(results: list[CaseResult]):
    """构造安全系数汇总图。"""
    case_labels = [f"工况{result.load_case.case_id}" for result in results]
    bearing_values = [round(result.bearing_sf, 3) if not math.isinf(result.bearing_sf) else None for result in results]
    average_values = [round(result.average_sf, 3) if not math.isinf(result.average_sf) else None for result in results]
    ecc_values = [round(result.actual_ecc_sf, 3) if not math.isinf(result.actual_ecc_sf) else None for result in results]
    ecc_required = [result.required_ecc_sf for result in results]

    return {
        "title": {"text": "主要安全系数汇总"},
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 24},
        "grid": {"left": "8%", "right": "6%", "bottom": "12%", "top": "22%"},
        "xAxis": {"type": "category", "data": case_labels},
        "yAxis": {"type": "value", "name": "安全系数"},
        "series": [
            {"name": "最大应力安全系数", "type": "bar", "data": bearing_values},
            {"name": "平均应力安全系数", "type": "bar", "data": average_values},
            {"name": "偏心距安全系数", "type": "bar", "data": ecc_values},
            {
                "name": "偏心距要求值",
                "type": "line",
                "data": ecc_required,
                "lineStyle": {"type": "dashed"},
            },
        ],
    }


@uzon_calc()
async def sheet():
    """JTG 3363-2019 矩形浅基础计算书示例。"""
    doc_title("JTG 3363-2019 矩形浅基础计算书")
    page_size("A4")

    H1("JTG 3363-2019 矩形浅基础计算书")
    Info("基于 uzoncalc 改写自原始 cpd 计算书，当前版本仅实现矩形平面截面。")

    """
    本示例将原 cpd 文件中的 Excel 轮廓点与基底反力输入，改写为 Python 变量定义。
    其中截面轮廓通过矩形截面计算器自动生成，图表统一使用 ECharts 绘制。
    """

    toc("目录")

    H2("设计参数")

    "设计规范：JTG 3363-2019"

    "修正后的地基承载力特征值："
    f_a = 300 * unit.kilopascal
    alias("f_a", "地基承载力特征值 f_a")

    H3("矩形截面输入")

    "基础宽度："
    width = 6 * unit.meter
    alias("width", "基础宽度 B")

    "基础高度："
    height = 8 * unit.meter
    alias("height", "基础高度 L")

    section = build_rectangle_section(width=width, height=height)

    H3("基底反力输入")

    load_cases = [
        LoadCase(
            case_id="1",
            Nz=100 * unit.kilonewton,
            Mx=-30 * unit.kilonewton * unit.meter,
            My=0 * unit.kilonewton * unit.meter,
            Hx=50 * unit.kilonewton,
            Hy=50 * unit.kilonewton,
            gamma_R=1.0,
            required_ecc_sf=1.0,
            required_overturn_sf=1.5,
            required_slide_sf=1.3,
        ),
        LoadCase(
            case_id="2",
            Nz=100 * unit.kilonewton,
            Mx=0 * unit.kilonewton * unit.meter,
            My=30 * unit.kilonewton * unit.meter,
            Hx=50 * unit.kilonewton,
            Hy=50 * unit.kilonewton,
            gamma_R=1.2,
            required_ecc_sf=1.2,
            required_overturn_sf=1.3,
            required_slide_sf=1.2,
        ),
        LoadCase(
            case_id="3",
            Nz=100 * unit.kilonewton,
            Mx=-30 * unit.kilonewton * unit.meter,
            My=30 * unit.kilonewton * unit.meter,
            Hx=50 * unit.kilonewton,
            Hy=50 * unit.kilonewton,
            gamma_R=1.5,
            required_ecc_sf=1.5,
            required_overturn_sf=1.2,
            required_slide_sf=1.2,
        ),
    ]

    Table(
        [[
            "工况",
            "Nz (kN)",
            "Mx (kN.m)",
            "My (kN.m)",
            "Hx (kN)",
            "Hy (kN)",
            "地基承载力抗力系数",
            "偏心距安全系数要求值",
            "抗倾覆安全系数输入值",
            "抗滑安全系数输入值",
        ]],
        [
            [
                load_case.case_id,
                f"{load_case.Nz.to(unit.kilonewton).magnitude:.2f}",
                f"{load_case.Mx.to(unit.kilonewton * unit.meter).magnitude:.2f}",
                f"{load_case.My.to(unit.kilonewton * unit.meter).magnitude:.2f}",
                f"{load_case.Hx.to(unit.kilonewton).magnitude:.2f}",
                f"{load_case.Hy.to(unit.kilonewton).magnitude:.2f}",
                f"{load_case.gamma_R:.2f}",
                f"{load_case.required_ecc_sf:.2f}",
                f"{load_case.required_overturn_sf:.2f}",
                f"{load_case.required_slide_sf:.2f}",
            ]
            for load_case in load_cases
        ],
        title="基底反力输入表",
    )

    H2("截面几何性质")

    "基础面积："
    A_sec = section.area
    alias("A_sec", "截面面积 A")

    "形心 x 坐标："
    x_cc = section.centroid_x
    alias("x_cc", "形心坐标 x_c")

    "形心 y 坐标："
    y_cc = section.centroid_y
    alias("y_cc", "形心坐标 y_c")

    "绕 x 轴惯性矩："
    I_x = section.inertia_x
    alias("I_x", "惯性矩 I_x")

    "绕 y 轴惯性矩："
    I_y = section.inertia_y
    alias("I_y", "惯性矩 I_y")

    "绕 x 轴截面抵抗矩："
    W_x = section.section_modulus_x
    alias("W_x", "截面抵抗矩 W_x")

    "绕 y 轴截面抵抗矩："
    W_y = section.section_modulus_y
    alias("W_y", "截面抵抗矩 W_y")

    Table(
        [["项目", "数值"]],
        [
            ["基础宽度 B", format_quantity(section.width, unit.meter)],
            ["基础高度 L", format_quantity(section.height, unit.meter)],
            ["截面面积 A", format_quantity(A_sec, unit.meter**2)],
            ["形心 x_c", format_quantity(x_cc, unit.meter)],
            ["形心 y_c", format_quantity(y_cc, unit.meter)],
            ["惯性矩 I_x", format_quantity(I_x, unit.meter**4)],
            ["惯性矩 I_y", format_quantity(I_y, unit.meter**4)],
            ["核心半宽 B/6", format_quantity(section.kern_x, unit.meter)],
            ["核心半高 L/6", format_quantity(section.kern_y, unit.meter)],
        ],
        title="矩形截面几何特征",
    )

    H2("截面示意图")

    """
    图中黑线为矩形基础轮廓，橙色虚线为核心区，蓝点为各工况荷载合力落点。
    若合力点位于核心区内，则该方向不会产生拉应力。
    """

    results = [evaluate_load_case(section, load_case, f_a) for load_case in load_cases]
    EChart(build_section_chart(section, results), height="460px")

    H2("工况验算")

    """
    对矩形基础按双向偏心受压公式计算四角基底应力：
    q = N / A ± M_x / W_x ± M_y / W_y
    然后取四角中的最大值与最小值作为基底控制应力。
    """

    for result in results:
        load_case = result.load_case

        H3(f"工况 {load_case.case_id}")

        inline()
        f"N_z = {load_case.Nz.to(unit.kilonewton).magnitude:.2f} kN，M_x = {load_case.Mx.to(unit.kilonewton * unit.meter).magnitude:.2f} kN.m，M_y = {load_case.My.to(unit.kilonewton * unit.meter).magnitude:.2f} kN.m"
        endInline()

        inline()
        f"偏心距 e_x = {result.ex.to(unit.meter).magnitude:.4f} m，e_y = {result.ey.to(unit.meter).magnitude:.4f} m"
        endInline()

        inline()
        f"基底平均应力 q_avg = {result.q_avg.to(unit.kilopascal).magnitude:.3f} kPa"
        endInline()

        inline()
        f"基底最小应力 q_min = {result.q_min.to(unit.kilopascal).magnitude:.3f} kPa"
        endInline()

        inline()
        f"基底最大应力 q_max = {result.q_max.to(unit.kilopascal).magnitude:.3f} kPa"
        endInline()

        inline()
        f"最大应力安全系数 K_1 = {format_float(result.bearing_sf, 3)}"
        endInline()

        inline()
        f"平均应力安全系数 K_2 = {format_float(result.average_sf, 3)}"
        endInline()

        inline()
        f"偏心距安全系数 K_3 = {format_float(result.actual_ecc_sf, 3)}，要求值为 {load_case.required_ecc_sf:.2f}"
        endInline()

        "抗倾覆安全系数与抗滑安全系数在当前版本中按输入表直接引用，后续可在补充抗倾覆力矩与抗滑摩阻参数后改为自动计算。"

        Table(
            [["项目", "结果", "判定"]],
            [
                [
                    "最大应力安全系数",
                    format_float(result.bearing_sf, 3),
                    "OK" if result.bearing_sf >= 1.0 else "NG",
                ],
                [
                    "平均应力安全系数",
                    format_float(result.average_sf, 3),
                    "OK" if result.average_sf >= 1.0 else "NG",
                ],
                [
                    "偏心距安全系数",
                    format_float(result.actual_ecc_sf, 3),
                    "OK" if result.actual_ecc_sf >= load_case.required_ecc_sf else "NG",
                ],
                [
                    "抗倾覆安全系数",
                    f"输入值 {load_case.required_overturn_sf:.2f}",
                    "引用输入值",
                ],
                [
                    "抗滑安全系数",
                    f"输入值 {load_case.required_slide_sf:.2f}",
                    "引用输入值",
                ],
            ],
            title=f"工况 {load_case.case_id} 验算结果",
        )

    H2("安全系数汇总")

    EChart(build_safety_chart(results), height="420px")

    Table(
        [[
            "工况",
            "q_max (kPa)",
            "q_min (kPa)",
            "K1 最大应力",
            "K2 平均应力",
            "K3 偏心距",
            "K3 要求值",
            "抗倾覆输入值",
            "抗滑输入值",
        ]],
        [
            [
                result.load_case.case_id,
                f"{result.q_max.to(unit.kilopascal).magnitude:.3f}",
                f"{result.q_min.to(unit.kilopascal).magnitude:.3f}",
                format_float(result.bearing_sf, 3),
                format_float(result.average_sf, 3),
                format_float(result.actual_ecc_sf, 3),
                f"{result.required_ecc_sf:.2f}",
                f"{result.overturn_sf:.2f}",
                f"{result.slide_sf:.2f}",
            ]
            for result in results
        ],
        title="浅基础安全系数汇总表",
    )

    H2("说明")

    """
    1. 本版计算书只实现矩形基础平面截面，轮廓点由截面计算器自动生成。

    2. 原 cpd 中的任意多边形截面压应力迭代算法没有迁移到当前脚本，因此这里采用矩形基础的直接公式进行验算。

    3. 抗倾覆与抗滑在当前输入条件下缺少自动计算所需的抗力臂、摩擦系数等参数，因此先按给定表格值展示。

    4. 后续若补充基础埋深、覆土重、底面摩擦系数、被动土压力等参数，可继续扩展为完整自动验算版本。
    """

    save("../output/JTG_3363_2019_shallow_foundation.html")


if __name__ == "__main__":
    ctx = run_sync(sheet)