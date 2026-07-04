from dataclasses import dataclass

from core.uzoncalc import enable_substitution, hide, run_sync, show, unit, uzon_calc


@dataclass(frozen=True)
class ConcreteGrade:
    """测试用混凝土等级参数。"""

    name: str
    fcd: float
    ftd: float
    elasticModulus: float
    beta: float
    epsilonCu: float


@uzon_calc()
async def attribute_substitution_sheet():
    """渲染属性访问和单位折叠共同参与的公式。"""
    hide()
    conc = ConcreteGrade(
        name="C50",
        fcd=100,
        ftd=100,
        elasticModulus=200000,
        beta=0.01,
        epsilonCu=0.01,
    )

    epsilon_cu = conc.epsilonCu
    x = 200
    beta = conc.beta
    show()

    enable_substitution()
    f_all = epsilon_cu * conc.elasticModulus * unit.MPa * (beta / x - 1.0)


def test_attribute_value_substitution_keeps_unit_product_parentheses():
    """属性值应在代入式中替换，单位折叠后的乘法因子应保留括号。"""
    ctx = run_sync(attribute_substitution_sheet)
    content = ctx.contents[-1]

    assert content.count(">conc.elasticModulus<") == 1
    assert "<mn>200000</mn>" in content
    assert content.count("<mo>(</mo>") >= 2
    assert content.count("<mo>)</mo>") >= 2
    assert "<mn>-1999.9</mn>" in content
