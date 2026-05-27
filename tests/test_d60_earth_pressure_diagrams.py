from examples.zh.d60_2015_earth_pressure_diagrams import (
    build_static_pressure_svg,
    build_active_pressure_svg,
    build_vehicle_active_pressure_svg,
)


def test_build_static_pressure_svg_keeps_core_labels():
    """验证静土压力示意图保留报告所需的主要结果标注。"""

    # 静土压力图重点体现三角形分布、底部强度和合力作用点。
    diagram_html = build_static_pressure_svg(
        height_value=6.0,
        depth_value=3.0,
        xi_value=0.5000,
        static_depth_pressure_value=27.0,
        static_earth_force_value=162.0,
        force_point_value=2.0,
    )

    assert diagram_html.startswith('<figure style="margin: 18px auto; max-width: 760px;">')
    assert "<svg" in diagram_html
    assert 'aria-label="静土压力示意图"' in diagram_html
    assert "H = 6.00 m" in diagram_html
    assert "h = 3.00 m" in diagram_html
    assert "ξ = 0.500" in diagram_html
    assert "e_j = 27.00 kPa" in diagram_html
    assert "E_j = 162.00 kN/m" in diagram_html
    assert "C = 2.00 m" in diagram_html
    assert "#7367f0" in diagram_html
    assert "#42b883" in diagram_html
    assert 'stroke="#7367f0" stroke-width="2"' in diagram_html
    assert diagram_html.count('stroke="#7367f0" stroke-width="2"') >= 6
    assert 'x1="150" y1="80" x2="166" y2="80"' in diagram_html
    assert 'x1="150" y1="342" x2="166" y2="342"' in diagram_html
    assert 'x1="150" y1="211" x2="166" y2="211"' in diagram_html
    assert 'x="360" y="116">ξ = 0.500</text>' in diagram_html
    assert 'x="430" y="236">e_j = 27.00 kPa</text>' in diagram_html
    assert 'x="430" y="262">E_j = 162.00 kN/m</text>' in diagram_html
    assert 'x="430" y="288">C = 2.00 m</text>' in diagram_html
    assert 'x="262" y="248">三角形静土压力分布</text>' in diagram_html


def test_build_active_pressure_svg_keeps_core_labels():
    """验证主动土压力示意图保留并优化报告需要的核心标注。"""

    # 只检查结构和关键标注，避免测试绑定具体 SVG 序列化细节。
    diagram_html = build_active_pressure_svg(
        height_value=6.0,
        width_value=1.0,
        mu_value=0.3333,
        active_force_value=108.0,
        force_point_value=2.0,
    )

    assert diagram_html.startswith('<figure style="margin: 18px auto; max-width: 760px;">')
    assert "<svg" in diagram_html
    assert 'aria-label="主动土压力示意图"' in diagram_html
    assert "H = 6.00 m" in diagram_html
    assert "B = 1.00 m" not in diagram_html
    assert "E = 108.00 kN" in diagram_html
    assert "C = 2.00 m" in diagram_html
    assert "μ = 0.333" in diagram_html
    assert '#7367f0' in diagram_html
    assert '#42b883' in diagram_html
    assert 'stroke="#7367f0" stroke-width="2"' in diagram_html
    assert diagram_html.count('stroke="#7367f0" stroke-width="2"') >= 6
    assert 'x1="150" y1="80" x2="166" y2="80"' in diagram_html
    assert 'x1="150" y1="342" x2="166" y2="342"' in diagram_html
    assert 'x="360" y="116">μ = 0.333</text>' in diagram_html
    assert 'x="430" y="252">E = 108.00 kN</text>' in diagram_html
    assert 'x="430" y="278">C = 2.00 m</text>' in diagram_html
    assert 'x="268" y="248">三角形侧压力分布</text>' in diagram_html


def test_build_vehicle_active_pressure_svg_keeps_core_labels():
    """验证汽车荷载主动土压力示意图保留并优化报告需要的核心标注。"""

    # 汽车荷载图需要额外检查等代土层和均布荷载标注。
    diagram_html = build_vehicle_active_pressure_svg(
        height_value=6.0,
        width_value=1.0,
        equivalent_height_value=0.6,
        mu_value=0.3333,
        vehicle_force_value=129.6,
        vehicle_point_value=2.1,
    )

    assert diagram_html.startswith('<figure style="margin: 18px auto; max-width: 760px;">')
    assert "<svg" in diagram_html
    assert 'aria-label="汽车荷载主动土压力示意图"' in diagram_html
    assert "h₀ = 0.60 m" in diagram_html
    assert "B = 1.00 m" not in diagram_html
    assert "E_q = 129.60 kN" in diagram_html
    assert "C_q = 2.10 m" in diagram_html
    assert ">q<" in diagram_html
    assert '#7367f0' in diagram_html
    assert '#42b883' in diagram_html
    assert 'stroke="#7367f0" stroke-width="2"' in diagram_html
    assert diagram_html.count('stroke="#7367f0" stroke-width="2"') >= 6
    assert 'x1="150" y1="122" x2="166" y2="122"' in diagram_html
    assert 'x1="150" y1="366" x2="166" y2="366"' in diagram_html
    assert 'x1="650" y1="78" x2="674" y2="78"' in diagram_html
    assert 'x1="650" y1="122" x2="674" y2="122"' in diagram_html
    assert 'x="420" y="74">q</text>' in diagram_html
