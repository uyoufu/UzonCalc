from matplotlib import pyplot as plt
from pint import UnitRegistry
from core.html_template import get_html_template
from core.setup import uzon_calc


@uzon_calc()
def sheet(*, unit: UnitRegistry):

    from core.utils.elements import p, div, span, input, plot
    from core.utils.options import hide, show, inline, endline

    length = 5 * unit.meter
    square_value = length**2

    q = 2.3 * unit.m**8 / (unit.s**2 * unit.kg) * 5 * unit.N * unit.m

    arr = [1, 2, 3, 4, 5]
    arr2 = [x**2 for x in arr]

    arr3 = [x + 1 for x in arr if x % 2 == 0]

    x_value = 1
    y_value = x_value + abs(-3) + (3 + 2) / 2 + 5**2

    z = -3

    "Welcome to UzonCalc calculation sheet."

    str1 = "Hello, "
    str2 = "UzonCalc!"
    # 包含纯加法时，可能是字符串拼接
    # 转换成函数调用实现
    # greeting = __add(str1, str2)
    greeting = str1 + str2

    # speed2 = 10 * unit.m / unit.second + (2 * unit.m / unit.second)**2
    # speed2 = 10*__format__(unit.m / unit.second) + (2*__format__(unit.m / unit.second))**2

    complex_number = 1 + 2j

    pint_unit = 10 * unit.meter

    join = "字符串1" + "字符串2"

    # 字母
    x_alpha = 100 * unit.meter
    x_Alpha = 200 * unit.meter

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

    from core.utils.options import inline, endline

    inline()
    "钢筋强度"
    h = 400 * unit.m
    b = 300 * unit.m
    f"截面尺寸2: b={b}, h={h}, 面积 A_s={b*h}"
    f"截面尺寸2: b={(b1 := 300*unit.m)}, h={(h1 := 400*unit.m)}, 面积 {(A_s1 :=b1*h1)}"
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
    timex = length / speed

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

    p(f"time = {timex}")


if __name__ == "__main__":
    import time

    # # tracemalloc 示例
    # import tracemalloc

    # tracemalloc.start()
    # # 执行你的转换/渲染工作

    t0 = time.perf_counter()
    props = {"field1"}  # 这里按你的业务填入 inputs
    # 异步调用 setup
    ctx = sheet()  # type: ignore
    print("\n".join(ctx.contents))

    html_content = get_html_template("\n".join(ctx.contents))
    # 保存为 HTML 文件
    with open("calculation_sheet.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    t1 = time.perf_counter()
    print(f"Execution time: {t1 - t0} seconds")

    # snapshot = tracemalloc.take_snapshot()
    # for stat in snapshot.statistics("lineno")[:10]:
    #     print(stat)
    # print("traced:", tracemalloc.get_traced_memory())
