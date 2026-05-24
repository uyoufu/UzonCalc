from __future__ import annotations

import math
from pathlib import Path

from uzoncalc import *


def format_diagram_number(value: float, digits: int = 2) -> str:
    """格式化示意图中的数值，避免图面出现过长小数。"""

    # 图面标注以工程常用精度显示，便于打印阅读。
    return f"{value:.{digits}f}"


def build_active_pressure_svg(
    *,
    height_value: float,
    width_value: float,
    mu_value: float,
    active_force_value: float,
    force_point_value: float,
) -> str:
    """生成无汽车荷载主动土压力 SVG 示意图。"""

    # 静态 SVG 直接内嵌到计算书，保证打印时保持矢量清晰度。
    height_label = format_diagram_number(height_value)
    width_label = format_diagram_number(width_value)
    force_label = format_diagram_number(active_force_value)
    point_label = format_diagram_number(force_point_value)
    mu_label = format_diagram_number(mu_value, 3)

    return f"""
<figure style="margin: 18px auto; max-width: 760px;">
  <svg viewBox="0 0 760 420" role="img" aria-label="主动土压力示意图" style="width: 100%; height: auto; font-family: Arial, 'Microsoft YaHei', sans-serif;">
    <defs>
      <linearGradient id="active-soil" x1="0" x2="1" y1="0" y2="1"><stop offset="0%" stop-color="#FDE68A" /><stop offset="100%" stop-color="#F59E0B" /></linearGradient>
      <linearGradient id="active-pressure" x1="0" x2="1" y1="0" y2="0"><stop offset="0%" stop-color="#93C5FD" stop-opacity="0.95" /><stop offset="100%" stop-color="#2563EB" stop-opacity="0.38" /></linearGradient>
      <marker id="active-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#DC2626" /></marker>
      <marker id="active-dim-arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 5 L 10 0 L 7 5 L 10 10 z" fill="#334155" /></marker>
    </defs>
    <rect x="8" y="8" width="744" height="404" rx="10" fill="#F8FAFC" stroke="#CBD5E1" />
    <text x="380" y="42" text-anchor="middle" font-size="22" font-weight="700" fill="#0F172A">主动土压力示意图</text>
    <polygon points="235,80 620,80 620,342 235,342" fill="url(#active-soil)" opacity="0.88" />
    <path d="M 235 80 L 620 80" stroke="#92400E" stroke-width="4" />
    <rect x="196" y="76" width="39" height="272" fill="#64748B" />
    <rect x="178" y="348" width="470" height="22" fill="#475569" />
    <polygon points="235,96 410,342 235,342" fill="url(#active-pressure)" stroke="#1D4ED8" stroke-width="2" />
    <line x1="276" y1="160" x2="235" y2="160" stroke="#2563EB" stroke-width="2" />
    <line x1="323" y1="226" x2="235" y2="226" stroke="#2563EB" stroke-width="2" />
    <line x1="379" y1="304" x2="235" y2="304" stroke="#2563EB" stroke-width="2" />
    <line x1="420" y1="260" x2="502" y2="260" stroke="#DC2626" stroke-width="3" marker-end="url(#active-arrow)" />
    <circle cx="420" cy="260" r="4" fill="#DC2626" />
    <line x1="166" y1="80" x2="166" y2="342" stroke="#334155" stroke-width="2" marker-start="url(#active-dim-arrow)" marker-end="url(#active-dim-arrow)" />
    <line x1="178" y1="80" x2="220" y2="80" stroke="#334155" stroke-width="1.5" />
    <line x1="178" y1="342" x2="220" y2="342" stroke="#334155" stroke-width="1.5" />
    <line x1="235" y1="388" x2="620" y2="388" stroke="#334155" stroke-width="2" marker-start="url(#active-dim-arrow)" marker-end="url(#active-dim-arrow)" />
    <text x="142" y="214" text-anchor="middle" font-size="17" font-weight="700" fill="#0F172A" transform="rotate(-90 142 214)">H = {height_label} m</text>
    <text x="428" y="382" text-anchor="middle" font-size="16" font-weight="700" fill="#0F172A">B = {width_label} m</text>
    <text x="470" y="252" font-size="17" font-weight="700" fill="#B91C1C">E = {force_label} kN</text>
    <text x="430" y="278" font-size="15" fill="#7F1D1D">C = {point_label} m</text>
    <text x="430" y="116" font-size="16" font-weight="700" fill="#1E3A8A">μ = {mu_label}</text>
    <text x="300" y="356" font-size="14" fill="#1E3A8A">三角形侧压力分布</text>
    <text x="520" y="112" font-size="15" fill="#78350F">填土</text>
    <text x="184" y="210" text-anchor="middle" font-size="15" fill="#F8FAFC" transform="rotate(-90 184 210)">墙背</text>
  </svg>
</figure>
"""


def build_vehicle_active_pressure_svg(
    *,
    height_value: float,
    width_value: float,
    equivalent_height_value: float,
    mu_value: float,
    vehicle_force_value: float,
    vehicle_point_value: float,
) -> str:
    """生成汽车荷载主动土压力 SVG 示意图。"""

    # 汽车荷载图单独绘制，避免与基本主动土压力标注互相拥挤。
    height_label = format_diagram_number(height_value)
    width_label = format_diagram_number(width_value)
    equivalent_height_label = format_diagram_number(equivalent_height_value)
    force_label = format_diagram_number(vehicle_force_value)
    point_label = format_diagram_number(vehicle_point_value)
    mu_label = format_diagram_number(mu_value, 3)

    return f"""
<figure style="margin: 18px auto; max-width: 760px;">
  <svg viewBox="0 0 760 450" role="img" aria-label="汽车荷载主动土压力示意图" style="width: 100%; height: auto; font-family: Arial, 'Microsoft YaHei', sans-serif;">
    <defs>
      <linearGradient id="vehicle-soil" x1="0" x2="1" y1="0" y2="1"><stop offset="0%" stop-color="#BBF7D0" /><stop offset="100%" stop-color="#16A34A" /></linearGradient>
      <linearGradient id="vehicle-load-layer" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#FCA5A5" stop-opacity="0.82" /><stop offset="100%" stop-color="#F97316" stop-opacity="0.72" /></linearGradient>
      <linearGradient id="vehicle-pressure" x1="0" x2="1" y1="0" y2="0"><stop offset="0%" stop-color="#C4B5FD" stop-opacity="0.95" /><stop offset="100%" stop-color="#7C3AED" stop-opacity="0.36" /></linearGradient>
      <marker id="vehicle-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#BE123C" /></marker>
      <marker id="vehicle-load-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#BE123C" /></marker>
      <marker id="vehicle-dim-arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 5 L 10 0 L 7 5 L 10 10 z" fill="#334155" /></marker>
    </defs>
    <rect x="8" y="8" width="744" height="434" rx="10" fill="#F8FAFC" stroke="#CBD5E1" />
    <text x="380" y="42" text-anchor="middle" font-size="22" font-weight="700" fill="#0F172A">汽车荷载主动土压力示意图</text>
    <rect x="235" y="78" width="385" height="44" fill="url(#vehicle-load-layer)" stroke="#EA580C" />
    <polygon points="235,122 620,122 620,366 235,366" fill="url(#vehicle-soil)" opacity="0.86" />
    <rect x="196" y="76" width="39" height="296" fill="#64748B" />
    <rect x="178" y="372" width="470" height="22" fill="#475569" />
    <polygon points="235,102 330,102 430,366 235,366" fill="url(#vehicle-pressure)" stroke="#6D28D9" stroke-width="2" />
    <line x1="302" y1="150" x2="235" y2="150" stroke="#7C3AED" stroke-width="2" />
    <line x1="346" y1="220" x2="235" y2="220" stroke="#7C3AED" stroke-width="2" />
    <line x1="395" y1="308" x2="235" y2="308" stroke="#7C3AED" stroke-width="2" />
    <line x1="430" y1="272" x2="512" y2="272" stroke="#BE123C" stroke-width="3" marker-end="url(#vehicle-arrow)" />
    <circle cx="430" cy="272" r="4" fill="#BE123C" />
    <line x1="166" y1="122" x2="166" y2="366" stroke="#334155" stroke-width="2" marker-start="url(#vehicle-dim-arrow)" marker-end="url(#vehicle-dim-arrow)" />
    <line x1="178" y1="122" x2="220" y2="122" stroke="#334155" stroke-width="1.5" />
    <line x1="178" y1="366" x2="220" y2="366" stroke="#334155" stroke-width="1.5" />
    <line x1="650" y1="78" x2="650" y2="122" stroke="#EA580C" stroke-width="2" marker-start="url(#vehicle-dim-arrow)" marker-end="url(#vehicle-dim-arrow)" />
    <line x1="235" y1="414" x2="620" y2="414" stroke="#334155" stroke-width="2" marker-start="url(#vehicle-dim-arrow)" marker-end="url(#vehicle-dim-arrow)" />
    <line class="vehicle-uniform-load-arrow" x1="280" y1="66" x2="280" y2="100" stroke="#BE123C" stroke-width="2.5" marker-end="url(#vehicle-load-arrow)" />
    <line class="vehicle-uniform-load-arrow" x1="320" y1="66" x2="320" y2="100" stroke="#BE123C" stroke-width="2.5" marker-end="url(#vehicle-load-arrow)" />
    <line class="vehicle-uniform-load-arrow" x1="360" y1="66" x2="360" y2="100" stroke="#BE123C" stroke-width="2.5" marker-end="url(#vehicle-load-arrow)" />
    <line class="vehicle-uniform-load-arrow" x1="400" y1="66" x2="400" y2="100" stroke="#BE123C" stroke-width="2.5" marker-end="url(#vehicle-load-arrow)" />
    <line class="vehicle-uniform-load-arrow" x1="440" y1="66" x2="440" y2="100" stroke="#BE123C" stroke-width="2.5" marker-end="url(#vehicle-load-arrow)" />
    <line class="vehicle-uniform-load-arrow" x1="480" y1="66" x2="480" y2="100" stroke="#BE123C" stroke-width="2.5" marker-end="url(#vehicle-load-arrow)" />
    <line class="vehicle-uniform-load-arrow" x1="520" y1="66" x2="520" y2="100" stroke="#BE123C" stroke-width="2.5" marker-end="url(#vehicle-load-arrow)" />
    <line class="vehicle-uniform-load-arrow" x1="560" y1="66" x2="560" y2="100" stroke="#BE123C" stroke-width="2.5" marker-end="url(#vehicle-load-arrow)" />
    <text x="590" y="74" font-size="16" font-weight="700" fill="#BE123C">q</text>
    <text x="142" y="246" text-anchor="middle" font-size="17" font-weight="700" fill="#0F172A" transform="rotate(-90 142 246)">H = {height_label} m</text>
    <text x="674" y="105" font-size="15" font-weight="700" fill="#9A3412">h₀ = {equivalent_height_label} m</text>
    <text x="428" y="408" text-anchor="middle" font-size="16" font-weight="700" fill="#0F172A">B = {width_label} m</text>
    <text x="486" y="263" font-size="17" font-weight="700" fill="#9F1239">E_q = {force_label} kN</text>
    <text x="438" y="290" font-size="15" fill="#7F1D1D">C_q = {point_label} m</text>
    <text x="440" y="148" font-size="16" font-weight="700" fill="#5B21B6">μ = {mu_label}</text>
    <text x="286" y="356" font-size="14" fill="#5B21B6">等代土层增强侧压力</text>
    <text x="502" y="152" font-size="15" fill="#14532D">填土</text>
    <text x="184" y="224" text-anchor="middle" font-size="15" fill="#F8FAFC" transform="rotate(-90 184 224)">墙背</text>
  </svg>
</figure>
"""


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
            Field("isColumn", "柱式墩台", FieldType.boolean, value=False),
            Field("gamma", "土的重度 γ (kN/m³)", FieldType.number, value=18.0),
            Field("phiDeg", "内摩擦角 φ (°)", FieldType.number, value=30.0),
            Field("heightH", "填土或计算土层高度 H (m)", FieldType.number, value=6.0),
            Field("depth", "静土压力计算深度 h (m)", FieldType.number, value=3.0),
            Field(
                "widthB",
                "桥台计算宽度或挡土墙长度 B (m)",
                FieldType.number,
                value=1.0,
                visible="(values)=>values.isColumn === false",
            ),
            Field("alphaDeg", "墙背与竖直面夹角 α (°)", FieldType.number, value=0.0),
            Field("betaDeg", "填土表面与水平面夹角 β (°)", FieldType.number, value=0.0),
            Field(
                "vehicleWheelWeightPerMeter",
                "汽车车轮横向单位总重 q (kN/m)",
                FieldType.number,
                value=10.8,
            ),
            Field(
                "columnCount",
                "柱数 n",
                FieldType.number,
                value=3,
                visible="(values)=>values.isColumn === true",
            ),
            Field(
                "columnSizeD",
                "柱直径或宽度 D (m)",
                FieldType.number,
                value=1.2,
                visible="(values)=>values.isColumn === true",
            ),
            Field(
                "columnSpacingLi",
                "柱间净距 li (m)",
                FieldType.number,
                value=1.5,
                visible="(values)=>values.isColumn === true",
            ),
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

    hide()
    rows = [
        [
            "土的重度",
            "γ",
            gammaSoil,
            "按调查或试验确定，默认取填土常用值",
        ],
        ["内摩擦角", "φ", phiDeg, "单位：°"],
        ["填土高度", "H", heightH, "静土压力与主动土压力计算高度"],
        ["计算深度", "h", depth, "静土压力强度计算点深度"],
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
    ]
    if inputs.isColumn:
        rows.extend(
            [
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
            ]
        )
    else:
        rows.append(["计算宽度或长度", "B", widthB, "桥台宽度或挡土墙长度"])
    show()

    Table(
        headers=["参数", "符号", "取值", "说明"],
        rows=rows,
        title="输入参数",
    )

    if inputs.isColumn:
        # 说明是柱式墩台，需要通过柱数、柱直径、柱间净距计算宽度
        # 当数据不满足时，提示输出错误并返回

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

    hide()
    # 提取带单位结果的纯数值，用于 SVG 图面标注。
    activePressureSvg = build_active_pressure_svg(
        height_value=heightH.to(unit.meter).magnitude,
        width_value=widthB.to(unit.meter).magnitude,
        mu_value=mu,
        active_force_value=activeEarthForce.to(unit.kN).magnitude,
        force_point_value=activeForcePoint.to(unit.meter).magnitude,
    )
    show()
    Div(activePressureSvg, classes="my-4")

    hide()
    vehicleApplicable = abs(betaDeg) < 1e-9
    show()

    if inputs.vehicleWheelWeightPerMeter > 0:
        H3("汽车荷载作用")
        "规范式 (4.2.3-6) 仅适用于土层特性无变化、桥台或挡土墙后有汽车荷载且 β = 0° 的情况。"

        alias("vehicleActiveEarthForce", "E_q")
        alias("vehicleForcePoint", "C_q")
        alias("vehicleEquivalentHeight", "h_0")

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
            hide()
            # 汽车荷载示意图仅在规范适用条件满足时输出。
            vehicleActivePressureSvg = build_vehicle_active_pressure_svg(
                height_value=heightH.to(unit.meter).magnitude,
                width_value=widthB.to(unit.meter).magnitude,
                equivalent_height_value=vehicleEquivalentHeight.to(
                    unit.meter
                ).magnitude,
                mu_value=mu,
                vehicle_force_value=vehicleActiveEarthForce.to(unit.kN).magnitude,
                vehicle_point_value=vehicleForcePoint.to(unit.meter).magnitude,
            )
            show()
            Div(vehicleActivePressureSvg, classes="my-4")
        else:
            Info(
                "当前 β 不为 0°，规范式 (4.2.3-6) 不适用，本节不计算汽车荷载主动土压力。"
            )

    alias("tanTheta", "tanθ")
    if vehicleApplicable:
        H3("破裂面角")
        "当 β = 0° 时，破坏棱体破裂面与竖直线间夹角 θ 的正切值可按式 (4.2.3-7) 计算。"

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
