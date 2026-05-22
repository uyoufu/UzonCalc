import ast

from core.uzoncalc.handcalc.ast_to_ir import expr_to_ir


def _render_expression_mathml(expression: str) -> str:
    """将表达式渲染为 MathML 字符串，便于断言节点样式。"""
    # 只解析表达式主体，避免测试依赖完整计算上下文。
    expression_node = ast.parse(expression, mode="eval").body
    return expr_to_ir(expression_node).to_mathml_xml()


def test_common_function_name_uses_function_name_class():
    """普通函数名应输出为专用 class，供模板设置颜色。"""
    mathml = _render_expression_mathml("sum([a, b])")

    assert 'class="function-name"' in mathml
    assert ">sum<" in mathml


def test_method_function_name_uses_function_name_class():
    """方法调用的方法名应输出为专用 class，点号不参与着色。"""
    mathml = _render_expression_mathml("section.resize(width)")

    assert 'class="function-name"' in mathml
    assert ">resize<" in mathml
    assert ">section<" in mathml
    assert ">.resize<" not in mathml


def test_math_module_function_hides_module_prefix():
    """math 模块函数展示时应去掉模块前缀，仅保留函数名。"""
    # 公式展示只转义 math. 前缀，不改变函数名本身的样式。
    mathml = _render_expression_mathml("math.sin(a)")

    assert 'class="function-name"' in mathml
    assert ">sin<" in mathml
    assert ">math<" not in mathml
    assert "<mo>.</mo>" not in mathml


def test_special_function_keeps_math_symbol_without_function_name_class():
    """特殊函数已转换为数学符号，不应再输出函数名样式。"""
    sqrt_mathml = _render_expression_mathml("sqrt(a)")
    abs_mathml = _render_expression_mathml("abs(a)")

    assert "<msqrt>" in sqrt_mathml
    assert 'class="function-name"' not in sqrt_mathml
    assert ">sqrt<" not in sqrt_mathml
    assert ">|<" in abs_mathml
    assert 'class="function-name"' not in abs_mathml
    assert ">abs<" not in abs_mathml
