from __future__ import annotations

import math
from pathlib import Path

from uzoncalc import *

OUTPUT_HTML = Path(__file__).with_name("d60_2015_earth_pressure_report.html")


def calculate_active_pressure_coefficient(
    phiDeg: float,
    alphaDeg: float,
    betaDeg: float,
    deltaDeg: float,
) -> float:
    """按 JTG D60-2015 式 4.2.3-5 计算主动土压力系数。"""
    phiRad = math.radians(phiDeg)
    alphaRad = math.radians(alphaDeg)
    betaRad = math.radians(betaDeg)
    deltaRad = math.radians(deltaDeg)

    numerator = math.cos(phiRad - alphaRad) ** 2
    radicalNumerator = math.sin(phiRad + deltaRad) * math.sin(phiRad - betaRad)
    radicalDenominator = math.cos(alphaRad + deltaRad) * math.cos(alphaRad - betaRad)
    radicalValue = radicalNumerator / radicalDenominator
    if radicalValue < 0:
        raise ValueError("主动土压力系数根号项为负，请检查 φ、α、β、δ 的取值。")

    bracketValue = 1 + math.sqrt(radicalValue)
    denominator = (
        math.cos(alphaRad) ** 2 * math.cos(alphaRad + deltaRad) * bracketValue**2
    )
    if abs(denominator) < 1e-12:
        raise ValueError("主动土压力系数分母接近 0，请检查墙背倾角和摩擦角。")
    return numerator / denominator


def calculate_failure_plane_tangent(
    phiDeg: float,
    alphaDeg: float,
    deltaDeg: float,
) -> float:
    """按 JTG D60-2015 式 4.2.3-7 计算破裂面角正切值。"""
    phiRad = math.radians(phiDeg)
    alphaRad = math.radians(alphaDeg)
    deltaRad = math.radians(deltaDeg)
    omegaRad = alphaRad + deltaRad + phiRad

    tanOmega = math.tan(omegaRad)
    tanAlpha = math.tan(alphaRad)
    cotPhi = 1 / math.tan(phiRad)
    radicalValue = (cotPhi + tanOmega) * (tanOmega - tanAlpha)
    if radicalValue < 0:
        raise ValueError("破裂面角根号项为负，请检查 φ、α、δ 的取值。")
    return -tanOmega + math.sqrt(radicalValue)


def validate_positive_number(value: float, fieldName: str) -> float:
    """统一校验工程参数，避免生成无物理意义的计算书。"""
    if value <= 0:
        raise ValueError(f"{fieldName} 应大于 0。")
    return value


def validate_nonnegative_number(value: float, fieldName: str) -> float:
    """统一校验允许取 0 的工程参数。"""
    if value < 0:
        raise ValueError(f"{fieldName} 不应小于 0。")
    return value


def format_quantity(value) -> str:
    """将 pint 量值压缩为适合表格展示的字符串。"""
    try:
        compactValue = value.to_compact()
    except Exception:
        compactValue = value
    return f"{compactValue:.3f}"


def format_number(value: float) -> str:
    """统一普通数值的小数位显示。"""
    return f"{value:.3f}"


@uzon_calc()
async def buildEarthPressureReport():
    doc_title("JTG D60-2015 土压力计算书")
    page_size("A4")
    font_family("Arial")

    H1("JTG D60-2015 土压力计算书")
    "本计算书依据 OCR 规范文档第 4.2.3 条“土的重力及土侧压力”编写，覆盖静土压力、主动土压力、汽车荷载、柱式墩台土压力计算宽度和压实填土压力。"
    "所有输入均提供默认值；工程应用时应以勘察、试验和设计文件参数替换默认值。"

    toc("目录")

    H2("1 计算输入")
    inputs = await UI(
        "土压力计算参数",
        [
            Field("gamma", "土的重度 γ (kN/m³)", FieldType.number, value=18.0),
            Field("phiDeg", "内摩擦角 φ (°)", FieldType.number, value=30.0),
            Field("heightH", "填土或计算土层高度 H (m)", FieldType.number, value=6.0),
            Field("depthh", "静土压力计算深度 h (m)", FieldType.number, value=3.0),
            Field(
                "widthB", "桥台计算宽度或挡土墙长度 B (m)", FieldType.number, value=1.0
            ),
            Field("alphaDeg", "墙背与竖直面夹角 α (°)", FieldType.number, value=0.0),
            Field("betaDeg", "填土表面与水平面夹角 β (°)", FieldType.number, value=0.0),
            Field("deltaDeg", "墙背与填土摩擦角 δ (°)", FieldType.number, value=15.0),
            Field(
                "vehicleEquivalentHeight",
                "汽车荷载等代土层厚度 h₀ (m)",
                FieldType.number,
                value=0.6,
            ),
            Field("columnCount", "柱数 n", FieldType.number, value=3),
            Field("columnSizeD", "柱直径或宽度 D (m)", FieldType.number, value=1.2),
            Field("columnSpacingLi", "柱间净距 li (m)", FieldType.number, value=1.5),
            Field(
                "compactedDepth", "压实填土计算深度 hq (m)", FieldType.number, value=3.0
            ),
        ],
    )

    # 先将输入转为计算变量，便于公式渲染和后续校验。
    gammaInput = validate_positive_number(float(inputs.gamma), "土的重度 γ")
    phiDeg = validate_positive_number(float(inputs.phiDeg), "内摩擦角 φ")
    heightInput = validate_positive_number(float(inputs.heightH), "填土高度 H")
    depthInput = validate_nonnegative_number(float(inputs.depthh), "静土压力计算深度 h")
    widthInput = validate_positive_number(float(inputs.widthB), "计算宽度或长度 B")
    alphaDeg = float(inputs.alphaDeg)
    betaDeg = float(inputs.betaDeg)
    deltaDeg = float(inputs.deltaDeg)
    vehicleHeightInput = validate_nonnegative_number(
        float(inputs.vehicleEquivalentHeight),
        "汽车荷载等代土层厚度 h₀",
    )
    columnCount = max(1, int(round(float(inputs.columnCount))))
    columnSizeInput = validate_positive_number(
        float(inputs.columnSizeD), "柱直径或宽度 D"
    )
    columnSpacingInput = validate_nonnegative_number(
        float(inputs.columnSpacingLi), "柱间净距 li"
    )
    compactedDepthInput = validate_nonnegative_number(
        float(inputs.compactedDepth), "压实填土计算深度 hq"
    )

    gammaSoil = gammaInput * unit.kN / unit.meter**3
    heightH = heightInput * unit.meter
    depthh = depthInput * unit.meter
    widthB = widthInput * unit.meter
    vehicleEquivalentHeight = vehicleHeightInput * unit.meter
    columnSizeD = columnSizeInput * unit.meter
    columnSpacingLi = columnSpacingInput * unit.meter
    compactedDepth = compactedDepthInput * unit.meter

    Table(
        headers=["参数", "符号", "取值", "说明"],
        rows=[
            [
                "土的重度",
                "γ",
                gammaSoil,
                "按调查或试验确定，默认取填土常用值",
            ],
            ["内摩擦角", "φ", f"{format_number(phiDeg)}°", "土性参数"],
            ["填土高度", "H", heightH, "静土压力与主动土压力计算高度"],
            ["计算深度", "h", depthh, "静土压力强度计算点深度"],
            ["计算宽度或长度", "B", widthB, "桥台宽度或挡土墙长度"],
            ["墙背倾角", "α", f"{format_number(alphaDeg)}°", "俯墙背为正"],
            [
                "填土坡角",
                "β",
                f"{format_number(betaDeg)}°",
                "台后或墙后主动土压力按正值",
            ],
            ["墙土摩擦角", "δ", f"{format_number(deltaDeg)}°", "默认按 φ/2 取值"],
            [
                "等代土层厚度",
                "h₀",
                format_quantity(vehicleEquivalentHeight),
                "用于汽车荷载主动土压力",
            ],
            ["柱数", "n", str(columnCount), "柱式墩台土压力计算宽度"],
            [
                "柱直径或宽度",
                "D",
                format_quantity(columnSizeD),
                "圆柱取直径，矩形柱取宽度",
            ],
            ["柱间净距", "li", format_quantity(columnSpacingLi), "相邻柱间净距"],
            [
                "压实填土深度",
                "hq",
                format_quantity(compactedDepth),
                "压实填土压力强度计算深度",
            ],
        ],
        title="输入参数",
    )

    H2("2 静土压力")
    "规范式 (4.2.3-1) 至 (4.2.3-3) 用于计算压实填土静土压力标准值。 E_j"

    alias("xi", "ξ")
    alias("gammaSoil", "γ")
    alias("depthh", "h")
    alias("heightH", "H")
    alias("staticDepthPressure", "e_j")
    alias("staticEarthForce", "E_j")

    sinPhi = math.sin(math.radians(phiDeg))
    xi = 1 - sinPhi
    staticDepthPressure = (xi * gammaSoil * depthh).to(unit.kPa)
    staticEarthForce = xi * gammaSoil * heightH**2 / 2

    Table(
        headers=["项目", "结果", "规范式"],
        rows=[
            ["静土压力系数 ξ", format_number(xi), "1 - sinφ"],
            [
                "深度 h 处静土压力 e_j",
                format_quantity(staticDepthPressure),
                "式 (4.2.3-1)",
            ],
            ["单位宽度静土压力 E_j", format_quantity(staticEarthForce), "式 (4.2.3-3)"],
        ],
        title="静土压力计算结果",
    )

    H2("3 主动土压力")
    "规范式 (4.2.3-4) 和 (4.2.3-5) 用于土层特性无变化且无汽车荷载时的主动土压力标准值。"

    alias("widthB", "B")
    alias("mu", "μ")
    alias("activeEarthForce", "E")
    alias("activeForcePoint", "C")

    mu = calculate_active_pressure_coefficient(phiDeg, alphaDeg, betaDeg, deltaDeg)
    activeEarthForce = widthB * mu * gammaSoil * heightH**2 / 2
    activeForcePoint = heightH / 3

    Table(
        headers=["项目", "结果", "规范式"],
        rows=[
            ["主动土压力系数 μ", format_number(mu), "式 (4.2.3-5)"],
            [
                "无汽车荷载主动土压力 E",
                format_quantity(activeEarthForce),
                "式 (4.2.3-4)",
            ],
            ["无汽车荷载作用点 C", format_quantity(activeForcePoint), "C = H/3"],
        ],
        title="主动土压力计算结果",
    )

    H3("3.1 汽车荷载作用")
    "规范式 (4.2.3-6) 仅适用于土层特性无变化、桥台或挡土墙后有汽车荷载且 β = 0° 的情况。"

    alias("vehicleActiveEarthForce", "E_q")
    alias("vehicleForcePoint", "C_q")
    alias("vehicleEquivalentHeight", "h_0")

    vehicleApplicable = abs(betaDeg) < 1e-9
    if vehicleApplicable:
        vehicleActiveEarthForce = (
            widthB
            * mu
            * gammaSoil
            * heightH
            * (heightH + 2 * vehicleEquivalentHeight)
            / 2
        )
        vehicleForcePoint = (
            heightH
            / 3
            * (heightH + 3 * vehicleEquivalentHeight)
            / (heightH + 2 * vehicleEquivalentHeight)
        )
        Table(
            headers=["项目", "结果", "规范式"],
            rows=[
                [
                    "汽车荷载主动土压力 E_q",
                    format_quantity(vehicleActiveEarthForce),
                    "式 (4.2.3-6)",
                ],
                [
                    "汽车荷载作用点 C_q",
                    format_quantity(vehicleForcePoint),
                    "C = H/3 × (H+3h₀)/(H+2h₀)",
                ],
            ],
            title="汽车荷载主动土压力计算结果",
        )
    else:
        Info("当前 β 不为 0°，规范式 (4.2.3-6) 不适用，本节不计算汽车荷载主动土压力。")

    H3("3.2 破裂面角")
    "当 β = 0° 时，破坏棱体破裂面与竖直线间夹角 θ 的正切值可按式 (4.2.3-7) 计算。"

    alias("tanTheta", "tanθ")
    if vehicleApplicable:
        tanTheta = calculate_failure_plane_tangent(phiDeg, alphaDeg, deltaDeg)
        Table(
            headers=["项目", "结果", "规范式"],
            rows=[
                ["破裂面角正切值 tanθ", format_number(tanTheta), "式 (4.2.3-7)"],
            ],
            title="破裂面角计算结果",
        )
    else:
        Info("当前 β 不为 0°，式 (4.2.3-7) 的适用条件不满足，本节不计算破裂面角。")

    H2("4 柱式墩台土压力计算宽度")
    "承受土侧压力的柱式墩台，作用在柱上的土压力计算宽度按柱间净距与柱直径或宽度的关系选取规范式。"

    alias("columnSizeD", "D")
    alias("columnSpacingLi", "l_i")
    alias("columnPressureWidth", "b")

    if columnSpacingLi <= columnSizeD:
        columnPressureWidth = (
            columnCount * columnSizeD + (columnCount - 1) * columnSpacingLi
        ) / columnCount
        columnFormula = "式 (4.2.3-8)"
        columnCondition = "li ≤ D"
    elif columnSizeD <= 1.0 * unit.meter:
        columnPressureWidth = columnSizeD * (2 * columnCount - 1) / columnCount
        columnFormula = "式 (4.2.3-9)"
        columnCondition = "li > D 且 D ≤ 1.0m"
    else:
        columnPressureWidth = (
            columnCount * (columnSizeD + 1.0 * unit.meter) - 1.0 * unit.meter
        ) / columnCount
        columnFormula = "式 (4.2.3-10)"
        columnCondition = "li > D 且 D > 1.0m"

    Table(
        headers=["项目", "结果", "说明"],
        rows=[
            ["采用条件", columnCondition, "按柱间净距和柱径判断"],
            [
                "每根柱土压力计算宽度 b",
                format_quantity(columnPressureWidth),
                columnFormula,
            ],
        ],
        title="柱式墩台土压力计算宽度",
    )

    H2("5 压实填土压力强度")
    "规范式 (4.2.3-11) 至 (4.2.3-13) 用于计算压实填土重力的竖向和水平压力强度标准值。"

    alias("lambdaCoeff", "λ")
    alias("verticalPressure", "q_v")
    alias("horizontalPressure", "q_h")

    lambdaCoeff = math.tan(math.radians(45 - phiDeg / 2)) ** 2
    verticalPressure = (gammaSoil * compactedDepth).to(unit.kPa)
    horizontalPressure = (lambdaCoeff * gammaSoil * compactedDepth).to(unit.kPa)

    Table(
        headers=["项目", "结果", "规范式"],
        rows=[
            ["侧压系数 λ", format_number(lambdaCoeff), "式 (4.2.3-13)"],
            ["竖向压力强度 q_v", format_quantity(verticalPressure), "式 (4.2.3-11)"],
            ["水平压力强度 q_h", format_quantity(horizontalPressure), "式 (4.2.3-12)"],
        ],
        title="压实填土压力强度计算结果",
    )

    H2("6 适用条件与说明")
    "土的重度和内摩擦角应根据调查或试验确定；无实际资料时可按规范推荐表或相关地基基础规范采用。"
    "土层特性有变化或受水位影响时，宜分层计算土的侧压力。"
    "本报告只计算土压力标准值和相关几何参数，不包含抗滑、抗倾覆、地基承载力或作用组合验算。"


if __name__ == "__main__":
    ctx = run_sync(buildEarthPressureReport)
    ctx.save(str(OUTPUT_HTML))
    print(f"已生成计算书：{OUTPUT_HTML}")
