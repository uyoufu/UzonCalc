from pint import UnitRegistry
from core.setup import uzon_calc


@uzon_calc()
def sheet(*, unit: UnitRegistry):

    from core.renders.elements import p, div, span, input
    from core.renders.options import hide, show

    speed2 = 10 * unit.m / unit.second + (2 * unit.m / unit.second)

    virtual_number = 1 + 2j

    pint_unit = 10 * unit.meter

    x_value = 1
    y_value = x_value + abs(-3) + (3 + 2) / 2 + 5**2

    p("calculation sheet started.")
    p(
        """
        this is a test paragraph.
        you can write **markdown** here.
        """
    )

    p("end of setup.")

    div("This is a div element.")

    span("This is a span element.")

    # 用户输入
    concrete__code = input("")
    selection = input("")
    f"混凝土强度: {concrete__code} MPa, 砂率: {selection} %"

    from core.renders.options import inline, endline

    inline()
    "钢筋强度"
    h = 400
    b = 300
    f"截面尺寸: b={b}, h={h}, 面积 A_s={b*h}"
    f"截面尺寸: b={(b := 300)} m, h={(h := 400)} m, 面积 {(A_s :=b*h)} m^2"
    endline()

    # 下标
    x_1 = 10
    x_abc = 20
    x_1_2 = 20

    a = 1

    b = 2

    c = a + b

    d = min(a, b)

    f"the min of a and b is {d}"

    # 带单位
    length = 5 * unit.meter
    speed = 10 * unit.m / unit.s
    time = length / speed

    square_value = length**2

    def sub_func(x, y):
        hide()
        x1 = 1
        x2 = 2
        show()

        x3 = x1 + x2

        return x + y

    total = sub_func(length, length)
    total

    p(f"time = {time}")


if __name__ == "__main__":
    import time

    t0 = time.perf_counter()
    props = {"field1"}  # 这里按你的业务填入 inputs
    # 异步调用 setup
    ctx = sheet()  # type: ignore
    print("\n".join(ctx.contents))
    t1 = time.perf_counter()
    print(f"Execution time: {t1 - t0} seconds")
