from dataclasses import dataclass
from pathlib import Path
import math
import sys

# 使用 pip 包时不需要该行；从仓库目录直接运行示例时用于定位本地包。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.uzoncalc import *  # noqa: E402,F403


@dataclass(frozen=True, slots=True)
class RectangleFoundation:
    """矩形基础平面尺寸，长度沿 x 方向，宽度沿 y 方向。"""

    length: float
    width: float

    @property
    def area(self) -> float:
        return self.length * self.width

    @property
    def inertia_x(self) -> float:
        return self.length * self.width**3 / 12

    @property
    def inertia_y(self) -> float:
        return self.width * self.length**3 / 12

    @property
    def edge_x(self) -> float:
        return self.length / 2

    @property
    def edge_y(self) -> float:
        return self.width / 2


@dataclass(frozen=True, slots=True)
class LoadCase:
    case_id: int
    Nz: float
    Mx: float
    My: float
    Hx: float
    Hy: float
    bearing_resistance_factor: float
    eccentric_limit: float
    overturning_safety_factor: float
    sliding_safety_factor: float


@dataclass(frozen=True, slots=True)
class LoadCaseResult:
    load_case: LoadCase
    sigma_avg: float
    sigma_max: float
    sigma_min: float
    bearing_safety_factor: float
    average_safety_factor: float
    eccentric_value: float
    eccentric_safety_factor: float
    status_bearing: str
    status_average: str
    status_eccentric: str


DEFAULT_LOAD_CASES = [
    LoadCase(1, 100, -30, 0, 50, 50, 1.0, 1.0, 1.5, 1.3),
    LoadCase(2, 100, 0, 30, 50, 50, 1.2, 1.2, 1.3, 1.2),
    LoadCase(3, 100, -30, 30, 50, 50, 1.5, 1.5, 1.2, 1.2),
]


def safe_divide(numerator: float, denominator: float) -> float:
    if math.isclose(denominator, 0.0):
        return math.inf
    return numerator / denominator


def evaluate_load_case(
    foundation: RectangleFoundation,
    load_case: LoadCase,
    bearing_capacity: float,
) -> LoadCaseResult:
    """按矩形基础双向偏心受压公式计算控制应力和安全系数。"""

    sigma_avg = load_case.Nz / foundation.area
    mx_stress = abs(load_case.Mx) * foundation.edge_y / foundation.inertia_x
    my_stress = abs(load_case.My) * foundation.edge_x / foundation.inertia_y

    # 四角应力取最不利组合，单位为 kN/m2，即 kPa。
    sigma_max = sigma_avg + mx_stress + my_stress
    sigma_min = sigma_avg - mx_stress - my_stress

    bearing_safety_factor = safe_divide(
        load_case.bearing_resistance_factor * bearing_capacity,
        sigma_max,
    )
    average_safety_factor = safe_divide(bearing_capacity, sigma_avg)
    eccentric_value = 1 - sigma_min * foundation.area / load_case.Nz
    eccentric_safety_factor = safe_divide(load_case.eccentric_limit, eccentric_value)

    return LoadCaseResult(
        load_case=load_case,
        sigma_avg=sigma_avg,
        sigma_max=sigma_max,
        sigma_min=sigma_min,
        bearing_safety_factor=bearing_safety_factor,
        average_safety_factor=average_safety_factor,
        eccentric_value=eccentric_value,
        eccentric_safety_factor=eccentric_safety_factor,
        status_bearing=check_status(bearing_safety_factor, 1.0),
        status_average=check_status(average_safety_factor, 1.0),
        status_eccentric=check_status(eccentric_safety_factor, 1.0),
    )


def check_status(value: float, limit: float) -> str:
    return "OK" if value >= limit else "NG"


def format_number(value: float, digits: int = 3) -> str:
    if math.isinf(value):
        return "∞"
    return f"{value:.{digits}f}"


def build_load_table_rows(load_cases: list[LoadCase]) -> list[list[str]]:
    return [
        [
            str(load_case.case_id),
            format_number(load_case.Nz, 2),
            format_number(load_case.Mx, 2),
            format_number(load_case.My, 2),
            format_number(load_case.Hx, 2),
            format_number(load_case.Hy, 2),
            format_number(load_case.bearing_resistance_factor, 2),
            format_number(load_case.eccentric_limit, 2),
            format_number(load_case.overturning_safety_factor, 2),
            format_number(load_case.sliding_safety_factor, 2),
        ]
        for load_case in load_cases
    ]


def build_summary_rows(results: list[LoadCaseResult]) -> list[list[str]]:
    return [
        [
            str(result.load_case.case_id),
            format_number(result.sigma_max),
            format_number(result.sigma_min),
            format_number(result.bearing_safety_factor),
            result.status_bearing,
            format_number(result.average_safety_factor),
            result.status_average,
            format_number(result.eccentric_safety_factor),
            result.status_eccentric,
        ]
        for result in results
    ]


@uzon_calc()
async def sheet():
    doc_title("JTG 3363-2019 矩形浅基础计算书")
    page_size("A4")

    H1("JTG 3363-2019 矩形浅基础计算书")
    Info("参考 Calcpad 示例迁移，当前版本仅实现矩形基础承载力与偏心距验算。")
    toc("目录")

    H2("输入参数")

    inputs = await UI(
        "矩形浅基础参数",
        [
            Field("length", "基础长度 L（m）", FieldType.number, value=8),
            Field("width", "基础宽度 B（m）", FieldType.number, value=6),
            Field(
                "bearingCapacity",
                "地基承载力特征值 f_a（kPa）",
                FieldType.number,
                value=300,
            ),
        ],
    )

    "基础长度："
    L = float(inputs.length) * unit.meter
    alias("L", "基础长度 L")

    "基础宽度："
    B = float(inputs.width) * unit.meter
    alias("B", "基础宽度 B")

    "修正后的地基承载力特征值："
    f_a = float(inputs.bearingCapacity) * unit.kilopascal
    alias("f_a", "地基承载力特征值 f_a")

    foundation = RectangleFoundation(
        length=L.to(unit.meter).magnitude, width=B.to(unit.meter).magnitude
    )
    bearing_capacity = f_a.to(unit.kilopascal).magnitude

    Table(
        [
            [
                "工况",
                "Nz（kN）",
                "Mx（kNm）",
                "My（kNm）",
                "Hx（kN）",
                "Hy（kN）",
                "地基承载力抗力系数",
                "偏心距安全系数",
                "抗倾覆安全系数",
                "抗滑安全系数",
            ]
        ],
        build_load_table_rows(DEFAULT_LOAD_CASES),
        title="基底反力输入表",
    )

    H2("矩形截面几何特征")

    "截面面积："
    A = L * B
    alias("A", "截面面积 A")

    "绕 x 轴惯性矩："
    I_x = L * B**3 / 12
    alias("I_x", "绕 x 轴惯性矩 I_x")

    "绕 y 轴惯性矩："
    I_y = B * L**3 / 12
    alias("I_y", "绕 y 轴惯性矩 I_y")

    Table(
        [["项目", "数值"]],
        [
            ["长度 L（沿 x 方向）", f"{foundation.length:.3f} m"],
            ["宽度 B（沿 y 方向）", f"{foundation.width:.3f} m"],
            ["面积 A", f"{foundation.area:.3f} m2"],
            ["惯性矩 Ix", f"{foundation.inertia_x:.3f} m4"],
            ["惯性矩 Iy", f"{foundation.inertia_y:.3f} m4"],
        ],
        title="截面几何参数",
    )

    H2("工况验算")

    """
    按矩形基础双向偏心受压公式计算基底应力。长度 L 沿 x 方向，宽度 B 沿 y 方向；
    My 产生 x 向偏心，Mx 产生 y 向偏心。当前版本对弯矩符号取绝对值组合控制最大、最小角点应力。
    """

    hide()
    results = [
        evaluate_load_case(foundation, load_case, bearing_capacity)
        for load_case in DEFAULT_LOAD_CASES
    ]
    show()

    # 输出表格
    Table(
        [
            [
                "工况",
                "σavg（kPa）",
                "σmax（kPa）",
                "σmin（kPa）",
                "K1 最大应力",
                "K1 判定",
                "K2 平均应力",
                "K2 判定",
                "偏心距验算值",
                "K3 偏心距",
                "K3 判定",
            ]
        ],
        [
            [
                str(result.load_case.case_id),
                format_number(result.sigma_avg),
                format_number(result.sigma_max),
                format_number(result.sigma_min),
                format_number(result.bearing_safety_factor),
                result.status_bearing,
                format_number(result.average_safety_factor),
                result.status_average,
                format_number(result.eccentric_value),
                format_number(result.eccentric_safety_factor),
                result.status_eccentric,
            ]
            for result in results
        ],
        title="工况计算结果汇总",
    )

    for result in results:
        load_case = result.load_case

        "基底平均应力："
        sigmaAvg = result.sigma_avg * unit.kilopascal
        alias("sigmaAvg", "基底平均应力 σ_avg")

        "基底最大应力："
        sigmaMax = result.sigma_max * unit.kilopascal
        alias("sigmaMax", "基底最大应力 σ_max")

        "基底最小应力："
        sigmaMin = result.sigma_min * unit.kilopascal
        alias("sigmaMin", "基底最小应力 σ_min")

        "基底最大应力安全系数："
        Kbearing = result.bearing_safety_factor
        alias("Kbearing", "最大应力安全系数 K_1")

        "仅计轴向荷载时基底平均应力安全系数："
        Kavg = result.average_safety_factor
        alias("Kavg", "平均应力安全系数 K_2")

        "偏心距验算值："
        eccentricValue = result.eccentric_value
        alias("eccentricValue", "偏心距验算值")

        "偏心距安全系数："
        Keccentric = result.eccentric_safety_factor
        alias("Keccentric", "偏心距安全系数 K_3")

        Table(
            [["项目", "结果", "判定"]],
            [
                ["最大应力安全系数 K1", format_number(Kbearing), result.status_bearing],
                ["平均应力安全系数 K2", format_number(Kavg), result.status_average],
                [
                    "偏心距安全系数 K3",
                    format_number(Keccentric),
                    result.status_eccentric,
                ],
                [
                    "抗倾覆安全系数",
                    f"{load_case.overturning_safety_factor:.2f}",
                    "仅展示",
                ],
                ["抗滑安全系数", f"{load_case.sliding_safety_factor:.2f}", "仅展示"],
            ],
            title=f"工况 {load_case.case_id} 验算结果",
        )

    H2("浅基础安全系数汇总")

    Table(
        [
            [
                "工况",
                "σmax（kPa）",
                "σmin（kPa）",
                "K1 最大应力",
                "K1 判定",
                "K2 平均应力",
                "K2 判定",
                "K3 偏心距",
                "K3 判定",
            ]
        ],
        build_summary_rows(results),
        title="浅基础安全系数汇总表",
    )

    H2("说明")
    """
    本计算书第一版仅迁移矩形截面承载力和偏心距验算。Hx、Hy、抗倾覆安全系数、
    抗滑安全系数按输入表展示，不参与自动判定；软弱地基和任意多边形截面算法未在本版实现。
    """

    save("../output/JTG_3363_2019_shallow_foundation.html")


if __name__ == "__main__":
    run_sync(sheet)
