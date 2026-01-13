from pathlib import Path
import sys

# Ensure project root is on sys.path so `import core` works when running
# this script from the `core` folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from matplotlib import pyplot as plt
from pint import UnitRegistry
from core.template.utils import get_html_template
from core.setup import uzon_calc


@uzon_calc()
def sheet(*, unit: UnitRegistry):

    from core.utils.elements import p, div, span, input, plot
    from core.utils.options import (
        hide,
        show,
        inline,
        endline,
        disable_substitution,
        enable_fstring_equation,
    )

    f"混凝土结构考虑容重 {(gamma_c := 26.5 * unit.kN / unit.m**3)}，由程序自动计算。"
    t_c = 10 * unit.cm
    hide()
    # 转换成 m
    t_c = t_c.to(unit.m)
    show()
    value = t_c * 8 * unit.m * gamma_c * 2

    from core.utils.doc import save

    save("../../output/example.html")


if __name__ == "__main__":
    import time

    t0 = time.perf_counter()
    props = {"field1"}  # 这里按你的业务填入 inputs
    # 异步调用 setup
    sheet()  # type: ignore
    t1 = time.perf_counter()
    print(f"Execution time: {t1 - t0} seconds")
