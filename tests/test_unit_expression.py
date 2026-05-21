import ast

from uzoncalc.handcalc.ast_to_ir import expr_to_ir


def _render_expression_mathml(expression: str) -> str:
    """将表达式渲染为 MathML，便于检查单位折叠结果。"""
    # 只解析表达式主体，避免测试依赖完整计算上下文。
    expression_node = ast.parse(expression, mode="eval").body
    return expr_to_ir(expression_node).to_mathml_xml()


def test_variable_unit_fraction_folds_unit_to_single_text():
    """变量参与单位乘除时，单位应折叠为 kN/m³。"""
    mathml = _render_expression_mathml("gammaInput * unit.kN / unit.meter**3")

    assert ">kN/m³<" in mathml
    assert "<mfrac>" not in mathml


def test_numeric_unit_fraction_keeps_existing_folded_unit():
    """纯数值单位表达式应保持原有折叠行为。"""
    mathml = _render_expression_mathml("18 * unit.kN / unit.meter**3")

    assert ">18<" in mathml
    assert ">kN/m³<" in mathml
    assert "<mfrac>" not in mathml


def test_multiple_non_unit_factors_share_single_unit_text():
    """多个非单位因子应保留乘积，并共用单一单位节点。"""
    mathml = _render_expression_mathml("a * b * unit.kN / unit.meter**3")

    assert ">a<" in mathml
    assert ">b<" in mathml
    assert ">kN/m³<" in mathml
    assert mathml.count('class="unit"') == 1


def test_non_unit_denominator_stays_fraction_with_folded_unit():
    """非单位分母应保留分数结构，单位仍折叠为单一节点。"""
    mathml = _render_expression_mathml("a * unit.kN / b / unit.meter**3")

    assert "<mfrac>" in mathml
    assert ">a<" in mathml
    assert ">b<" in mathml
    assert ">kN/m³<" in mathml
    assert mathml.count('class="unit"') == 1
