from __future__ import annotations

import math
from pathlib import Path

from uzoncalc import *


@uzon_calc()
async def sheet():
    doc_title("JTG D60-2015 土压力计算书")
    page_size("A4")
    font_family("Arial")

    H1("JTG D60-2015 土压力计算书")

    "本计算书依据 OCR 规范文档第 4.2.3 条“土的重力及土侧压力”编写，覆盖静土压力、主动土压力、汽车荷载、柱式墩台土压力计算宽度和压实填土压力。"
    "所有输入均提供默认值；工程应用时应以勘察、试验和设计文件参数替换默认值。"

    toc("目录")

    H2("计算输入")
    inputs = await UI(
        "土压力计算参数",
        [
            Field("gamma", "土的重度 γ (kN/m³)", FieldType.number, value=18.0),
            Field("phiDeg", "内摩擦角 φ (°)", FieldType.number, value=30.0),
            Field("heightH", "填土或计算土层高度 H (m)", FieldType.number, value=6.0),
            Field("depth", "静土压力计算深度 h (m)", FieldType.number, value=3.0),
            Field(
                "widthB", "桥台计算宽度或挡土墙长度 B (m)", FieldType.number, value=1.0
            ),
            Field("alphaDeg", "墙背与竖直面夹角 α (°)", FieldType.number, value=0.0),
            Field("betaDeg", "填土表面与水平面夹角 β (°)", FieldType.number, value=0.0),
            Field(
                "vehicleWheelWeightPerMeter",
                "汽车车轮横向单位总重 q (kN/m)",
                FieldType.number,
                value=10.8,
            ),
            Field("columnCount", "柱数 n", FieldType.number, value=3),
            Field("columnSizeD", "柱直径或宽度 D (m)", FieldType.number, value=1.2),
            Field("columnSpacingLi", "柱间净距 li (m)", FieldType.number, value=1.5),
            Field(
                "compactedDepth", "压实填土计算深度 hq (m)", FieldType.number, value=3.0
            ),
        ],
    )

    hide()
    # 添加单位
    # 输入同步完成类型转换和单位附加，便于公式渲染和后续校验。
    gammaSoil = inputs.gamma * unit.kN / unit.meter**3
    phiDeg = inputs.phiDeg
    heightH = inputs.heightH * unit.meter
    depth = inputs.depth * unit.meter
    widthB = inputs.widthB * unit.meter
    alphaDeg = inputs.alphaDeg
    betaDeg = inputs.betaDeg
    deltaDeg = phiDeg / 2
    vehicleWheelWeight = inputs.vehicleWheelWeightPerMeter * unit.kN / unit.meter
    columnCount = max(1, int(inputs.columnCount))
    columnSizeD = inputs.columnSizeD * unit.meter
    columnSpacingLi = inputs.columnSpacingLi * unit.meter
    compactedDepth = inputs.compactedDepth * unit.meter
    vehicleUnitLength = 1.0 * unit.meter
    vehicleEquivalentHeight = vehicleWheelWeight / vehicleUnitLength / gammaSoil
    show()

    Table(
        headers=["参数", "符号", "取值", "说明"],
        rows=[
            [
                "土的重度",
                "γ",
                gammaSoil,
                "按调查或试验确定，默认取填土常用值",
            ],
            ["内摩擦角", "φ", phiDeg, "单位：°"],
            ["填土高度", "H", heightH, "静土压力与主动土压力计算高度"],
            ["计算深度", "h", depth, "静土压力强度计算点深度"],
            ["计算宽度或长度", "B", widthB, "桥台宽度或挡土墙长度"],
            ["墙背倾角", "α", alphaDeg, "单位：°，俯墙背为正"],
            [
                "填土坡角",
                "β",
                betaDeg,
                "单位：°，台后或墙后主动土压力按正值",
            ],
            ["墙土摩擦角", "δ", deltaDeg, "单位：°，按 δ=φ/2 计算"],
            ["汽车车轮总重", "q", vehicleWheelWeight, "横向单位宽度重量"],
            [
                "等代土层厚度",
                "h_0",
                vehicleEquivalentHeight,
                "按 q/(γ×1m) 计算",
            ],
            ["柱数", "n", str(columnCount), "柱式墩台土压力计算宽度"],
            [
                "柱直径或宽度",
                "D",
                columnSizeD,
                "圆柱取直径，矩形柱取宽度",
            ],
            ["柱间净距", "li", columnSpacingLi, "相邻柱间净距"],
            [
                "压实填土深度",
                "hq",
                compactedDepth,
                "压实填土压力强度计算深度",
            ],
        ],
        title="输入参数",
    )

    H2("静土压力")
    "规范式 (4.2.3-1) 至 (4.2.3-3) 用于计算压实填土静土压力标准值。"

    alias("xi", "ξ")
    alias("gammaSoil", "γ")
    alias("depth", "h")
    alias("heightH", "H")
    alias("staticDepthPressure", "e_j")
    alias("staticEarthForce", "E_j")

    sinPhi = math.sin(math.radians(phiDeg))
    xi = 1 - sinPhi
    staticDepthPressure = (xi * gammaSoil * depth).to(unit.kPa)
    staticEarthForce = xi * gammaSoil * heightH**2 / 2

    Table(
        headers=["项目", "结果", "规范式"],
        rows=[
            ["静土压力系数 ξ", xi, "1 - sinφ"],
            [
                "深度 h 处静土压力 e_j",
                staticDepthPressure,
                "式 (4.2.3-1)",
            ],
            ["单位宽度静土压力 E_j", staticEarthForce, "式 (4.2.3-3)"],
        ],
        title="静土压力计算结果",
    )

    H2("主动土压力")
    "规范式 (4.2.3-4) 和 (4.2.3-5) 用于土层特性无变化且无汽车荷载时的主动土压力标准值。"

    alias("widthB", "B")
    alias("mu", "μ")
    alias("activeEarthForce", "E")
    alias("activeForcePoint", "C")

    alias("phiRad", "φ")
    alias("alphaRad", "α")
    alias("betaRad", "β")
    alias("deltaRad", "δ")

    # 规范式直接在报告流程中展开，保证公式步骤随计算书输出。
    phiRad = math.radians(phiDeg)
    alphaRad = math.radians(alphaDeg)
    betaRad = math.radians(betaDeg)
    deltaRad = math.radians(deltaDeg)

    activeCoefficientNumerator = math.cos(phiRad - alphaRad) ** 2

    activeCoefficientDenominator = (
        (math.cos(alphaRad) ** 2)
        * math.cos(alphaRad + deltaRad)
        * (
            1
            + math.sqrt(
                math.sin(phiRad + deltaRad)
                * math.sin(phiRad - betaRad)
                / (math.cos(alphaRad + deltaRad) * math.cos(alphaRad - betaRad))
            )
        )
    )

    mu = activeCoefficientNumerator / activeCoefficientDenominator
    activeEarthForce = widthB * mu * gammaSoil * heightH**2 / 2
    activeForcePoint = heightH / 3

    Table(
        headers=["项目", "结果", "规范式"],
        rows=[
            ["主动土压力系数 μ", mu, "式 (4.2.3-5)"],
            [
                "无汽车荷载主动土压力 E",
                activeEarthForce,
                "式 (4.2.3-4)",
            ],
            ["无汽车荷载作用点 C", activeForcePoint, "C = H/3"],
        ],
        title="主动土压力计算结果",
    )

    H3("汽车荷载作用")
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
                    "等代土层厚度 h₀",
                    vehicleEquivalentHeight,
                    "h₀ = q/(γ×1m)",
                ],
                [
                    "汽车荷载主动土压力 E_q",
                    vehicleActiveEarthForce,
                    "式 (4.2.3-6)",
                ],
                [
                    "汽车荷载作用点 C_q",
                    vehicleForcePoint,
                    "C = H/3 × (H+3h₀)/(H+2h₀)",
                ],
            ],
            title="汽车荷载主动土压力计算结果",
        )
    else:
        Info("当前 β 不为 0°，规范式 (4.2.3-6) 不适用，本节不计算汽车荷载主动土压力。")

    H3("破裂面角")
    "当 β = 0° 时，破坏棱体破裂面与竖直线间夹角 θ 的正切值可按式 (4.2.3-7) 计算。"

    alias("tanTheta", "tanθ")
    if vehicleApplicable:
        # 破裂面角按式 (4.2.3-7) 展开计算，便于计算书记录中间步骤。
        omegaRad = alphaRad + deltaRad + phiRad
        tanOmega = math.tan(omegaRad)
        tanAlpha = math.tan(alphaRad)
        cotPhi = 1 / math.tan(phiRad)
        failurePlaneRadical = (cotPhi + tanOmega) * (tanOmega - tanAlpha)
        if failurePlaneRadical < 0:
            raise ValueError("破裂面角根号项为负，请检查 φ、α、δ 的取值。")
        tanTheta = -tanOmega + math.sqrt(failurePlaneRadical)
        Table(
            headers=["项目", "结果", "规范式"],
            rows=[
                ["破裂面角正切值 tanθ", tanTheta, "式 (4.2.3-7)"],
            ],
            title="破裂面角计算结果",
        )
    else:
        Info("当前 β 不为 0°，式 (4.2.3-7) 的适用条件不满足，本节不计算破裂面角。")

    H2("柱式墩台土压力计算宽度")
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
                columnPressureWidth,
                columnFormula,
            ],
        ],
        title="柱式墩台土压力计算宽度",
    )

    H2("压实填土压力强度")
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
            ["侧压系数 λ", lambdaCoeff, "式 (4.2.3-13)"],
            ["竖向压力强度 q_v", verticalPressure, "式 (4.2.3-11)"],
            ["水平压力强度 q_h", horizontalPressure, "式 (4.2.3-12)"],
        ],
        title="压实填土压力强度计算结果",
    )

    H2("适用条件与说明")
    "土的重度和内摩擦角应根据调查或试验确定；无实际资料时可按规范推荐表或相关地基基础规范采用。"
    "土层特性有变化或受水位影响时，宜分层计算土的侧压力。"
    "本报告只计算土压力标准值和相关几何参数，不包含抗滑、抗倾覆、地基承载力或作用组合验算。"


if __name__ == "__main__":
    ctx = run_sync(sheet)
    html_path = Path(__file__).with_name("d60_2015_earth_pressure_report.html")
    ctx.save(str(html_path))
    print(f"已生成计算书：{html_path}")
