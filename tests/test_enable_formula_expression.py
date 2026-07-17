import html
import re

from uzoncalc import *


def get_xi_limit(concrete_name: str, tension_kind: str) -> float:
    """返回测试用的相对受压区高度限值。"""
    return 0.518


def _plain_text(content: str) -> str:
    """将 HTML/MathML 内容转换为便于断言的纯文本。"""
    return html.unescape(re.sub(r"<[^>]+>", "", content)).replace(" ", "")


@uzon_calc()
async def formula_expression_toggle_sheet():
    concrete_name = "C40"
    tension_kind = "HRB400"
    full_xi_limit = get_xi_limit(concrete_name, tension_kind)

    disable_formula_expression()
    substituted_xi_limit = get_xi_limit(concrete_name, tension_kind)

    disable_substitution()
    result_only_xi_limit = get_xi_limit(concrete_name, tension_kind)

    enable_substitution()
    enable_formula_expression()
    restored_xi_limit = get_xi_limit(concrete_name, tension_kind)


@uzon_calc()
async def fstring_formula_expression_disabled_sheet():
    enable_fstring_equation()
    disable_formula_expression()

    left_value = 1
    right_value = 2
    f"result {left_value + right_value}"


def test_formula_expression_is_rendered_by_default():
    """默认显示原始公式表达式、代入表达式和最终结果。"""
    ctx = run_sync(formula_expression_toggle_sheet)
    content = _plain_text(ctx.contents[2])

    assert "fullxilimit=get_xi_limit(concretename,tensionkind)" in content
    assert "get_xi_limit(C40,HRB400)" in content
    assert content.endswith("=0.518")


def test_disable_formula_expression_keeps_substitution_and_result():
    """关闭原始公式表达式后，仍显示值代入和结果。"""
    ctx = run_sync(formula_expression_toggle_sheet)
    content = _plain_text(ctx.contents[3])

    assert "substitutedxilimit=get_xi_limit(C40,HRB400)=0.518" in content
    assert "get_xi_limit(concretename,tensionkind)" not in content


def test_disable_formula_expression_with_substitution_disabled_keeps_result():
    """同时关闭原始表达式和代入时，赋值语句仍显示结果。"""
    ctx = run_sync(formula_expression_toggle_sheet)
    content = _plain_text(ctx.contents[4])

    assert content == "resultonlyxilimit=0.518"


def test_enable_formula_expression_restores_original_expression():
    """重新启用原始公式表达式后恢复完整渲染。"""
    ctx = run_sync(formula_expression_toggle_sheet)
    content = _plain_text(ctx.contents[-1])

    assert "restoredxilimit=get_xi_limit(concretename,tensionkind)" in content
    assert "get_xi_limit(C40,HRB400)" in content
    assert content.endswith("=0.518")


def test_fstring_equation_mode_respects_formula_expression_toggle():
    """f-string 方程模式关闭原始表达式时仍保留代入表达式和结果。"""
    ctx = run_sync(fstring_formula_expression_disabled_sheet)
    content = ctx.contents[-1]
    text = _plain_text(content)

    assert text == "result1+2=3"
    assert "leftvalue+rightvalue" not in text
    assert "<math" in content
