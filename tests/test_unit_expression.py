import ast

from uzoncalc.handcalc.ast_to_ir import expr_to_ir


def _render_expression_mathml(expression: str) -> str:
    """将表达式渲染为 MathML，便于检查单位折叠结果。"""
    # 只解析表达式主体，避免测试依赖完整计算上下文。
    expression_node = ast.parse(expression, mode="eval").body
    return expr_to_ir(expression_node).to_mathml_xml()


def test_variable_unit_fraction_attaches_unit_to_variable():
    """变量参与单位乘除时，单位应附着到相邻变量。"""
    mathml = _render_expression_mathml("gammaInput * unit.kN / unit.meter**3")

    assert ">gammaInput<" in mathml
    assert ">kN/m³<" in mathml
    assert "<mfrac>" not in mathml


def test_numeric_unit_fraction_attaches_unit_to_number():
    """数值单位表达式应显示为带单位数值。"""
    mathml = _render_expression_mathml("18 * unit.kN / unit.meter**3")

    assert ">18<" in mathml
    assert ">kN/m³<" in mathml
    assert "<mfrac>" not in mathml


def test_unit_attaches_to_nearest_previous_factor():
    """多个非单位因子中，单位应附着到源码中最近的前置因子。"""
    mathml = _render_expression_mathml("a * b * unit.kN / unit.meter**3")

    assert ">a<" in mathml
    assert ">b<" in mathml
    assert ">kN/m³<" in mathml
    assert mathml.count('class="unit"') == 1
    assert mathml.index(">b<") < mathml.index(">kN/m³<")


def test_unit_product_parenthesizes_low_precedence_factor():
    """单位局部绑定后，加减表达式因子仍应按乘法上下文补括号。"""
    mathml = _render_expression_mathml("a * unit.MPa * (b / c - 1.0)")

    assert "<mo>(</mo>" in mathml
    assert "<mo>)</mo>" in mathml
    assert ">MPa<" in mathml


def test_unit_product_keeps_plain_product_without_extra_parentheses():
    """普通乘除单位表达式不应因上下文传递增加无意义括号。"""
    mathml = _render_expression_mathml("a * unit.MPa * b / c")

    assert "<mo>(</mo>" not in mathml
    assert "<mo>)</mo>" not in mathml
    assert ">MPa<" in mathml


def test_non_unit_denominator_keeps_local_denominator_unit():
    """非单位分母应保留分数结构，分母单位附着到分母因子。"""
    mathml = _render_expression_mathml("a * unit.kN / b / unit.meter**3")

    assert "<mfrac>" in mathml
    assert ">a<" in mathml
    assert ">b<" in mathml
    assert ">kN<" in mathml
    assert ">m³<" in mathml
    assert mathml.count('class="unit"') == 2
    assert mathml.index(">a<") < mathml.index(">kN<")
    assert mathml.index(">b<") < mathml.index(">m³<")


def test_unit_product_keeps_unit_next_to_attribute_factor():
    """属性值与单位相乘时，单位应保持在属性因子旁边。"""
    mathml = _render_expression_mathml(
        "epsilon_cu * conc.elasticModulus * unit.MPa / 10 * (beta / x - 1.0)"
    )

    assert ">conc.elasticModulus<" in mathml
    assert ">MPa<" in mathml
    assert ">10<" in mathml
    assert mathml.index(">conc.elasticModulus<") < mathml.index(">MPa<")
    assert mathml.index(">MPa<") < mathml.index(">10<")


def test_denominator_only_unit_stays_in_fraction_denominator():
    """纯分母单位不应被渲染成前一个变量的 1/unit 后缀。"""
    mathml = _render_expression_mathml("a / unit.second")

    assert "<mfrac>" in mathml
    assert ">a<" in mathml
    assert ">s<" in mathml
    assert mathml.index(">a<") < mathml.index(">s<")


def test_grouped_unit_power_folds_to_single_unit_text():
    """组合单位整体幂次应折叠为单一单位节点。"""
    mathml = _render_expression_mathml("(unit.kN / unit.meter) ** 2")

    assert ">kN²/m²<" in mathml
    assert mathml.count('class="unit"') == 1
    assert "<msup>" not in mathml


def test_non_unit_factor_with_grouped_unit_power_uses_single_unit_text():
    """非单位因子和组合单位幂次共存时，单位应附着到该因子。"""
    mathml = _render_expression_mathml("a * (unit.kN / unit.meter) ** 2")

    assert ">a<" in mathml
    assert ">kN²/m²<" in mathml
    assert mathml.count('class="unit"') == 1
    assert "<msup>" not in mathml


def test_dimensionless_unit_cancellation_returns_only_non_unit_part():
    """单位完全抵消时仅保留非单位部分。"""
    mathml = _render_expression_mathml("a * unit.meter / unit.meter")

    assert ">a<" in mathml
    assert 'class="unit"' not in mathml


def test_zero_power_unit_product_renders_as_one():
    """含单位乘积的零次幂应正规化为 1。"""
    mathml = _render_expression_mathml("(a * unit.meter) ** 0")

    assert ">1<" in mathml
    assert 'class="unit"' not in mathml


def test_parenthesized_unit_denominator_folds_to_single_unit_text():
    """括号内多个分母单位应折叠为单一单位节点。"""
    mathml = _render_expression_mathml("unit.kN / (unit.meter * unit.second)")

    assert ">kN/m/s<" in mathml
    assert mathml.count('class="unit"') == 1
