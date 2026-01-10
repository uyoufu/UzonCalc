from matplotlib import pyplot as plt
from pint import UnitRegistry
from core.html_template import get_html_template
from core.setup import uzon_calc


@uzon_calc()
def sheet(*, unit: UnitRegistry):

    from core.utils.elements import p, div, span, input, plot
    from core.utils.options import hide, show, inline, endline

    inline(", ")
    "钢筋强度"
    h = 400 * unit.m
    b = 300 * unit.m
    f"面积 {(A_s:=b*h)}"
    endline()

    from core.utils.doc import save

    save("output/example.html")


if __name__ == "__main__":
    import time

    t0 = time.perf_counter()
    props = {"field1"}  # 这里按你的业务填入 inputs
    # 异步调用 setup
    sheet()  # type: ignore
    t1 = time.perf_counter()
    print(f"Execution time: {t1 - t0} seconds")
